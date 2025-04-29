
#include <stdio.h>
#include <time.h>
#include <sched.h>


long measure_sleep_resolution() {
    struct timespec nano_sleep, start, end;
    nano_sleep.tv_sec = 0;
    nano_sleep.tv_nsec = 1;
    int num_iterations = 1000;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < num_iterations; i++){
    clock_nanosleep(CLOCK_MONOTONIC, 0, &nano_sleep, NULL);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    return ((end.tv_nsec - start.tv_nsec)/num_iterations);
}

int main(int argc, char **argv)
{

  printf("Actual Resolution:  %ld ns\n", measure_sleep_resolution());

}

