#include <stdio.h>
#include <stdlib.h>

#ifndef PPOS
#include "ppos.h"
#endif

#ifndef QUEUE
#include "queue.h"
#endif

task_t main_task, *current_task, *suspended_head, *ready_head;
int task_count;

void ppos_init () 
{
    task_count = 0;

    /* desativa o buffer da saida padrao (stdout), usado pela função printf */
    setvbuf (stdout, 0, _IONBF, 0) ;

    suspended_head = NULL;
    ready_head = NULL;
     
    main_task.id = 0;
    getcontext(&(main_task.context));
    current_task = &main_task;
}

// Cria uma nova tarefa. Retorna um ID> 0 ou erro.
int task_create (task_t *task,			
                 void (*start_routine)(void *),
                 void *arg)
{
    getcontext(&(task->context));

    char *stack;
    stack = malloc (STACKSIZE) ;
    if (stack)
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

    makecontext (&(task->context), (void*)(*start_routine), 1, arg) ;
    task->id = ++task_count;
    task->status = 0;

    queue_append((queue_t**) &ready_head, (queue_t*) &task);

#ifdef DEBUG
    printf("\ntask_count: %d, task->id: %d\n", task_count, task->id);
#endif

    return task->id;
}

// Termina a tarefa corrente, indicando um valor de status encerramento
void task_exit (int exit_code) 
{
    if( exit_code == 0 )
    {
	task_switch(&main_task);
    }
}

// alterna a execução para a tarefa indicada
int task_switch (task_t *task) 
{
#ifdef DEBUG
    printf("\ncurrent_task->id: %d, next_task->id: %d\n", current_task->id, task->id);
#endif
    queue_remove((queue_t**)&ready_head, (queue_t*)&task);
    task->status = 1;
    current_task->status = 3;
    task_t *aux = current_task;
    current_task = task;
    swapcontext(&(aux->context), &(task->context));
    return 0;
}

// retorna o identificador da tarefa corrente (main deve ser 0)
int task_id ()
{
    return current_task->id;
}

void task_yield ()
{
    queue_append((queue_t**)&ready_head, (queue_t*)&current_task);
}

task_t* scheduler ()
{
    
}

