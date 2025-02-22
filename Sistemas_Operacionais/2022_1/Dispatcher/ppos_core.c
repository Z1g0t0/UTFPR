#include <stdio.h>
#include <stdlib.h>
#include "queue.h"

#ifndef PPOS
#include "ppos.h"
#endif

//#define DEBUG

task_t main_task, dispatcher_task, *current_task, *ready_q; 

int userTasks;

task_t* scheduler ()
{
    int size = queue_size((queue_t*)ready_q);
#ifdef DEBUG
    printf("\n------------ SCHEDULER ------------\nready_q size: %d\n", size);
#endif
    if( size > 0 )
    {
	ready_q = ready_q->next;
	return ready_q->prev;
    }
    else
    {
	return NULL;
    }
}    

void dispatcher()
{
    while( userTasks > 0 )
    {
	task_t *next = scheduler();
	if( next )
	{
#ifdef DEBUG
    printf("\n------------ DISPATCHER ------------\nnext->id: %d\n", next->id);
#endif
	    task_switch(next);
	    if( next->status == 5 )
    	        free((&next->context)->uc_stack.ss_sp);
	}
    }
    task_exit(0);
}

void ppos_init () 
{
#ifdef DEBUG
    printf("\n\n------------ PPOS INIT ------------\n\n");
#endif

    /* desativa o buffer da saida padrao (stdout), usado pela função printf */
    setvbuf (stdout, 0, _IONBF, 0) ;

    ready_q = NULL;
    userTasks = 0;
    current_task = &main_task;
    task_create(&dispatcher_task, (void *)dispatcher, NULL);
}

// Cria uma nova tarefa. Retorna um ID> 0 ou erro.
int task_create( task_t *task,			
                 void (*start_routine)(void *),
                 void *arg)
{
    getcontext(&task->context);

    char *stack;
    stack = malloc (STACKSIZE) ;
    if ( stack )
    {
       task->context.uc_stack.ss_sp = stack ;
       task->context.uc_stack.ss_size = STACKSIZE;
       task->context.uc_stack.ss_flags = 0 ;
       task->context.uc_link = 0;
    }
    else
    {
       perror ("Erro na criação da pilha: ") ;
       exit (1) ;
    }

    makecontext (&task->context, (void*)(*start_routine), 1, arg) ;

    if( task != &dispatcher_task )
    {
	queue_append((queue_t**) &ready_q, (queue_t*) task);
	task->id = ++userTasks;
    	task->status = 1;
    }
    else
    {
	dispatcher_task.id = -1;
    }

#ifdef DEBUG
    printf("\n------------ TASK CREATE ------------\ntask_count: %d - task->id: %d\n", userTasks, task->id);
#endif

    return task->id;
}

// retorna o identificador da tarefa corrente (main deve ser 0)
int task_id () { return current_task->id; }

// Termina a tarefa corrente, indicando um valor de status encerramento
void task_exit (int exit_code) 
{
    if( exit_code == 0 )
    {
	if( current_task == &dispatcher_task )
    	{
    	    task_switch(&main_task);
    	}
	else
	{
	    current_task->status = 5;
	    --userTasks;
	    task_yield();
	}
    }
    else
    {
	printf("\nERRO: task_exit - CODE = %d\n", exit_code);
    }
}

// alterna a execução para a tarefa indicada
int task_switch (task_t *task) 
{
#ifdef DEBUG
    printf("\n------------ TASK SWITCH ------------\ncurrent_task->id: %d - next_task->id: %d\n", current_task->id, task->id);
#endif

    if ( task == &main_task )
    {
	if( current_task != &dispatcher_task )
	{
	    printf("\nERRO\n");
	    return -1;
	}
	swapcontext(&dispatcher_task.context, &main_task.context);
    }
    else if( current_task == &main_task )
    {
	current_task = &dispatcher_task;
	swapcontext(&main_task.context, &dispatcher_task.context);
    }
    else if( task == &dispatcher_task )
    {
	if( current_task->status != 5 ) 
	{
	    current_task->status = 1;
	    queue_append((queue_t**)&ready_q, (queue_t*)current_task);
	}
    	task_t* aux = current_task;
	current_task = &dispatcher_task;
    	swapcontext(&aux->context, &current_task->context);
    }
    else
    {
	if( current_task != &dispatcher_task )
	{
	    printf("\nERRO\n");
	    return -1;
	}
	queue_remove((queue_t**)&ready_q, (queue_t*)task);
    	task_t* aux = current_task;
	current_task = task;
    	swapcontext(&aux->context, &current_task->context);
    }
    
    return 0;
}

void task_yield ()
{
    if( current_task != &dispatcher_task )
	task_switch(&dispatcher_task);
    else
	printf("\n???\n");
}

void print_elem (void *ptr)
{
   task_t *elem = ptr ;

   if (!elem)
      return ;

   elem->prev ? printf ("%d", elem->prev->id) : printf ("*") ;
   printf ("<%d>", elem->id) ;
   elem->next ? printf ("%d", elem->next->id) : printf ("*") ;
}
