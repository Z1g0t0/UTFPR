#include <stdio.h>
#include <stdlib.h>
#include "queue.h"

int queue_size (queue_t *queue)
{
    if( !queue )
    {
	return 0;
    }

    else if( queue->next == queue )
    {
	return 1;
    }
    
    else
    {
	queue_t* head = queue;
    	queue_t* aux = queue->next; 
    	int i = 2;

    	while( aux->next != head )
    	{
    	    aux = aux->next;
    	    i++;
    	}
	return i; 
    }
}

void queue_print (char *name, queue_t *queue, void print_elem (void*) )
{
    if( !queue )
    {
    	printf("%s: [", name);
	print_elem(NULL);	
    	printf("]\n");
    }


    else if( queue_size( queue ) == 1 )
    {
	print_elem( queue );
    }

    else
    {
    	queue_t* aux = queue; 

    	printf("%s: [", name);

	do
    	{
	    print_elem(aux);
	    printf(" ");
	    aux = aux->next;
    	}
    	while( aux != queue );

    	printf("]\n");
    }	
}

int queue_append (queue_t **queue, queue_t *elem)
{
    if ( !elem )
    {
	printf("Elemento NULL!\n");
	return -1;
    }

    if ( !(*queue) )
    {
	*queue = elem;
	(*queue)->next = *queue;
	(*queue)->prev = *queue;
    }

    if ( *queue )
    {
	if ( (elem->prev || elem->next ) && queue_size( (*queue) ) != 1 )
	{
	    fprintf(stderr, "Elemento pertencente a outra fila.\n");
	    return -1;
	}
	else
	{
	    if ( queue_size( (*queue) ) == 1 )
	    {
		(*queue)->prev = elem;
		(*queue)->next = elem;
		elem->prev = (*queue);
		elem->next = (*queue);
	    }
	    else
	    {
		queue_t* first = *queue;
    	    	queue_t* aux = (*queue)->next;

    	    	while( aux->next != first )
    	    	{
    	    	    aux = aux->next;
    	    	}
    	    	
    	    	aux->next = elem;
    	    	elem->prev = aux;
    	    	elem->next = first;
    	    	first->prev = elem;
	    }
	}
    }

    return 0;
}

int queue_remove (queue_t **queue, queue_t *elem)
{
    if ( !elem )
    {
	fprintf(stderr, "Elemento NULL!\n");
	return -1;
    }

    else if ( !(*queue) )
    {
	fprintf(stderr, "Fila vazia!\n");
	return -1;
    }


    else if( queue_size( (*queue) ) == 1 )
    {
	if ( *queue == elem )
	{
	    (*queue)->prev = NULL;
    	    (*queue)->next = NULL;
    	    *queue = NULL;
	}
	else
	{
	    fprintf(stderr, "Elemento nao encontrado!\n");
	    return -1;
	}
    }

    else
    {
	if ( *queue == elem )
	{
	   queue_t* prev = (*queue)->prev;
    	   queue_t* next = (*queue)->next;

	   prev->next = next;
	   next->prev = prev;

	   (*queue)->prev = NULL;
	   (*queue)->next = NULL;
	   *queue = next;
	}

	else
	{
	   queue_t* prev = (*queue);
    	   queue_t* aux = (*queue)->next;
    	   queue_t* next = aux->next;
    	   while( aux != elem )
    	   {
	       prev = aux;
    	       aux = next;
	       next = aux->next;
    	   }
	   if( aux == (*queue) )
	   {
	       fprintf(stderr, "\nElemento nao encontrado.\n");
	       return -1;
	   }
    	   
    	   prev->next = next;
    	   next->prev = prev;
	   aux->prev = NULL;
	   aux->next = NULL;
	   aux = NULL;
	}
    }

    return 0;
}

