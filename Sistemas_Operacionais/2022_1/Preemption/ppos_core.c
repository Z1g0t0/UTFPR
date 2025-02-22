//#define DEBUG

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/time.h>
#include "queue.h"

#ifndef PPOS
#include "ppos.h"
#endif


task_t main_task, dispatcher_task, *current_task, *ready_q; 
int userTasks, alpha, ticks;

// estrutura que define um tratador de sinal (deve ser global ou static)
struct sigaction action ;

// estrutura de inicialização to timer
struct itimerval timer;

task_t* scheduler ()
{
    int size = queue_size((queue_t*)ready_q);
#ifdef DEBUG
    printf("\n------------ SCHEDULER ------------\nready_q size: %d\n", size);
#endif

    if( size > 0 )
    {	
	task_t *parser = ready_q;
	int i;
	for(i = 0; i < userTasks; i++)
	{
	    parser->dyn_prio += alpha;
#ifdef DEBUG
    printf("\nPARSER->ID: %d - PRIO: %d\n", parser->id, parser->dyn_prio);
#endif
	    parser = parser->next;
	}

	task_t *lesser = ready_q;
	int parser_prio, lesser_prio;
	for(i = 0; i < userTasks; i++)
	{
	    parser = parser->next;
	    parser_prio = parser->dyn_prio;
	    lesser_prio = lesser->dyn_prio; 
	    if( ( parser_prio == lesser_prio && parser->id < lesser->id ) ||  parser_prio < lesser_prio ) 
	    {
		lesser = parser;
	    }
	}
#ifdef DEBUG
    printf("\nLESSER->ID: %d - PRIO: %d\n", lesser->id, lesser->dyn_prio);
#endif
	lesser->dyn_prio = lesser->base_prio;	

	return lesser;
    } 
    else
    {
	return NULL;
    }
}    

void tick_handler( int signum ) 
{
    if ( current_task->preemptable == 1 ) 
    {
	if ( ticks == 0 )
	    task_switch(&dispatcher_task);
	else
	    ticks--;
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
	    ticks = QUANTUM;		//definido em ppos_data
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
    alpha = -1;
    current_task = &main_task;
    task_create(&dispatcher_task, (void *)dispatcher, NULL);

    action.sa_handler = tick_handler;
    sigemptyset (&action.sa_mask) ;
    action.sa_flags = 0 ;

    if( sigaction (SIGALRM, &action, 0) < 0 )
    {
	perror ("Erro em sigaction: ") ;
      	exit (1) ;
    }

    // ajusta valores do temporizador
    timer.it_value.tv_usec = 1 ;      // primeiro disparo, em micro-segundos
    timer.it_value.tv_sec  = 0 ;      // primeiro disparo, em segundos
    timer.it_interval.tv_usec = 1000 ;   // disparos subsequentes, em micro-segundos
    timer.it_interval.tv_sec  = 0 ;   // disparos subsequentes, em segundos

    // arma o temporizador ITIMER_REAL (vide man setitimer)
    if( setitimer (ITIMER_REAL, &timer, 0) < 0 )
    {
	perror ("Erro em setitimer: ") ;
      	exit (1) ;
    }

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
	task->preemptable = 1;
	task->base_prio = 0;
	task->dyn_prio = 0;
    }
    else
    {
	dispatcher_task.id = -1;
	dispatcher_task.preemptable = 0;
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
    printf("\n------------ TASK SWITCH ------------\ncurrent_task->id: %d |>>>| next_task->id: %d\n", current_task->id, task->id);
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

// define a prioridade estática de uma tarefa (ou a tarefa atual)
void task_setprio (task_t *task, int prio)
{
    if( task )
	task->base_prio = task->dyn_prio = prio;
    else
	current_task->base_prio = current_task->dyn_prio = prio;
}

// retorna a prioridade estática de uma tarefa (ou a tarefa atual)
int task_getprio (task_t *task)
{
    if( task )
	return task->base_prio;
    else
	return current_task->base_prio;
}

void print_elem (void *ptr)
{
   task_t *elem = ptr ;

   if ( !elem )
      return ;

   elem->prev ? printf ("%d", elem->prev->id) : printf ("*") ;
   printf ("<%d>", elem->id) ;
   elem->next ? printf ("%d", elem->next->id) : printf ("*") ;
}
