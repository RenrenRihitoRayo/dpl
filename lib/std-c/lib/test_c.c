#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef struct Person Person;

struct Person {
    char *  name;
    int age;
    void (*init)(Person * self, const char * name, int age);
    void (*greet)(Person * self);
    void (*destroy)(Person * self);
};

void __ceq_method_Person_init(Person * self, char * name, int age) {
        self->name = (char*)malloc(sizeof(char) * strlen(name)+1);
        strcpy(self->name, name);
        self->age = age;
}

void __ceq_method_Person_greet(Person * self) {
printf("Hello, I am %s (%d)\n", self->name, self->age);
}

void __ceq_method_Person_destroy(Person * self) {
free(self->name);
free(self);
}

void __ceq_bind_Person(Person* self) {
    self->init = __ceq_method_Person_init;
    self->greet = __ceq_method_Person_greet;
    self->destroy = __ceq_method_Person_destroy;
}

int
main
(
)
{
    Person* human = (Person*)malloc(sizeof(Person));
    __ceq_bind_Person(human);
    human->init(human, "Andrew" , 16);
    human->greet(human);
    human->destroy(human);
return
0
;
}