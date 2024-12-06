#include <stdbool.h>
#include <stdlib.h>
#include <string.h> 
#define MAX 10000

typedef struct {
    int top;
    char items[MAX];
} Stack;

void initStack(Stack *arr) {
    arr->top = -1;
}

bool isEmpty(Stack* arr) {
    return arr->top == -1;
}
void push(Stack *arr, char item) {
    if (arr->top < (MAX - 1)) {
        arr->items[++(arr->top)] = item;
    } else {
        exit(0); 
    }
}

char pop(Stack* arr) {
    if (!isEmpty(arr)) {
        return arr->items[(arr->top)--];
    } else {
        exit(0);
    }
}
bool isValid(char* s) {
    Stack arr;
    initStack(&arr);
    if  (strlen(s) % 2 != 0){
        return false;
        exit(0);
    }
    for (int i = 0; i < strlen(s); i++) {
        if (s[i] == '(' || s[i] == '{' || s[i] == '[') {
            push(&arr, s[i]);
        } else {
            if (isEmpty(&arr)) {
                return false;
            }
            char topChar = pop(&arr);
            if ((topChar == '(' && s[i] != ')') || 
                (topChar == '{' && s[i] != '}') || 
                (topChar == '[' && s[i] != ']')) {
                return false;
            }
        }
    }
    return isEmpty(&arr);
}
