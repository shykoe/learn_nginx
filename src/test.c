#include <stdio.h>
#include <string.h>
#include "ngx_palloc.h"
int main(int argc,char* argv[]){
  printf(sizeof(struct ngx_pool_s));
  return 0;
}