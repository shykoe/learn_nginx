一个nginx学习记录(个人笔记)
===
##已完成
> * [ngx_string](#ngx_string)
> * [ngx_palloc](#ngx_palloc)
> * [ngx_array](#ngx_array)
> * [ngx_queue](#ngx_queue)
> * [ngx_list](#ngx_list)
> * [ngx_hash](#ngx_hash)
> * [ngx_radix_tree](#ngx_radix_tree)
> * [ngx_rbtree](#ngx_rbtree)

ngx_string
----------
```c
typedef struct {
    size_t      len;
    u_char     *data;
} ngx_str_t;
#define ngx_string(str)     { sizeof(str) - 1, (u_char *) str }
```
ngxinx使用自己实现的string,由len指定string的长度,由宏ngx_string实现普通字符串与ngx风格字符串的转换.

ngx_palloc
----------
```c
typedef struct {
    u_char               *last;//当前内存池分配到此处，即下一次分配从此处开始  
    u_char               *end;//内存池结束位置  
    ngx_pool_t           *next;//内存池里面有很多块内存，这些内存块就是通过该指针连成链表的  
    ngx_uint_t            failed;//内存池分配失败次数  
} ngx_pool_data_t;//内存池的数据块位置信息  


struct ngx_pool_s {//内存池头部结构  ngx_pool_t
    ngx_pool_data_t       d;//内存池的数据块  
    size_t                max;//内存池数据块可用的最大值  
    ngx_pool_t           *current;//指向当前内存池  
    ngx_chain_t          *chain;//该指针挂接一个ngx_chain_t结构  
    ngx_pool_large_t     *large; //大块内存链表，即分配空间超过max的内存  
    ngx_pool_cleanup_t   *cleanup;//释放内存池的callback  
    ngx_log_t            *log;//日志信息  
};
```
结构如图
![](http://hi.csdn.net/attachment/201107/5/0_1309882017mTT4.gif)
```c
ngx_pool_t *ngx_create_pool(size_t size, ngx_log_t *log);//创建内存池
void ngx_destroy_pool(ngx_pool_t *pool);//销毁
void ngx_reset_pool(ngx_pool_t *pool);//

void *ngx_palloc(ngx_pool_t *pool, size_t size);//返回内存池对齐的位置的可用内存
void *ngx_pnalloc(ngx_pool_t *pool, size_t size);//返回非对齐位置的可用内存
void *ngx_pcalloc(ngx_pool_t *pool, size_t size);
void *ngx_pmemalign(ngx_pool_t *pool, size_t size, size_t alignment);//申请alignment对齐的size大小内存并挂载到large链表首
ngx_int_t ngx_pfree(ngx_pool_t *pool, void *p);//释放所有large_t的内存
```
####调用ngx_create_pool创建内存池
```c
ngx_pool_t *
ngx_create_pool(size_t size, ngx_log_t *log)
{
    ngx_pool_t  *p;

    p = ngx_memalign(NGX_POOL_ALIGNMENT, size, log);//使用posix_memalign申请对齐的内存(其实malloc申请的也是对齐的内存,不过此函数的选择多些) 地址为NGX_POOL_ALIGNMENT的倍数，大小为size，返回申请地址
    if (p == NULL) {
        return NULL;
    }

    p->d.last = (u_char *) p + sizeof(ngx_pool_t);//指向ngx_pool_t结构体之后的位置
    p->d.end = (u_char *) p + size;//内存池结束位置
    p->d.next = NULL;//初始状态下块内存地址为null
    p->d.failed = 0;//初始失败次数为0

    size = size - sizeof(ngx_pool_t);//可使用的空间减去ngx_pool_t的大小
    p->max = (size < NGX_MAX_ALLOC_FROM_POOL) ? size : NGX_MAX_ALLOC_FROM_POOL;//NGX_MAX_ALLOC_FROM_POOL为getpagesize()定义一般为4kb

    p->current = p;
    p->chain = NULL;
    p->large = NULL;
    p->cleanup = NULL;
    p->log = log;

    return p;
}

```
例如，调用ngx_create_pool(1024, 0x80d1c4c)后，创建的内存池物理结构如下图。
![](http://hi.csdn.net/attachment/201107/5/0_1309882022ZpNM.gif)
####分配内存
```c
static ngx_inline void *
ngx_palloc_small(ngx_pool_t *pool, size_t size, ngx_uint_t align)
{
    u_char      *m;
    ngx_pool_t  *p;

    p = pool->current;

    do {
        m = p->d.last;

        if (align) {
            m = ngx_align_ptr(m, NGX_ALIGNMENT);
            /*NGX_ALIGNMENT为unsignedlong大小 
            ngx_align_ptr(p, a)  (u_char *) (((uintptr_t) (p) + ((uintptr_t) a - 1)) & ~((uintptr_t) a - 1))
            NGX_ALIGNMENT为2的N次幂~((uintptr_t) a - 1)n+1位为1后n位为0 与上 p+a-1 使得m位置为 NGX_ALIGNMENT倍(即令m的位置内存对齐 提高寻址速度)
            */
        }

        if ((size_t) (p->d.end - m) >= size) {//剩余块内空间大于需要分配的空间则分配返回
            p->d.last = m + size;

            return m;
        }

        p = p->d.next;//不足查找下块

    } while (p);

    return ngx_palloc_block(pool, size);//都不够则新建一块ngx_pool_t挂载链表上
}


static void *
ngx_palloc_block(ngx_pool_t *pool, size_t size)//申请新的一块ngx_pool_t挂载链表上
{
    u_char      *m;
    size_t       psize;
    ngx_pool_t  *p, *new;

    psize = (size_t) (pool->d.end - (u_char *) pool);//计算pool的大小 

    m = ngx_memalign(NGX_POOL_ALIGNMENT, psize, pool->log);//分配一块与pool大小相同的内存 
    if (m == NULL) {
        return NULL;
    }

    new = (ngx_pool_t *) m;

    new->d.end = m + psize;
    new->d.next = NULL;
    new->d.failed = 0;

    m += sizeof(ngx_pool_data_t);//让m指向该块内存ngx_pool_data_t结构体之后数据区起始位置  导致此处新建的last起始位置与create出的起始位置不同
    m = ngx_align_ptr(m, NGX_ALIGNMENT);//对齐
    new->d.last = m + size;

    for (p = pool->current; p->d.next; p = p->d.next) {
        if (p->d.failed++ > 4) {//failed的值只在此处被修改  
            pool->current = p->d.next;//失败4次以上移动current指针  
        }
    }

    p->d.next = new;

    return m;
}
```
内存池的物理结构
![alt text](https://raw.githubusercontent.com/shykoe/reading_nginx/master/src/core/ngx_pool_t.jpg)
ngx_array
---------
```c
typedef struct {
    void        *elts;//数组数据区起始位置  
    ngx_uint_t   nelts;//实际存放的元素个数
    size_t       size; //每个元素大小  
    ngx_uint_t   nalloc; //数组所含空间个数，即实际分配的小空间的个数,也是申请时能容纳的最大大小  
    ngx_pool_t  *pool; //该数组在此内存池中分配  
} ngx_array_t;


ngx_array_t *ngx_array_create(ngx_pool_t *p, ngx_uint_t n, size_t size);//创建数组,个数n
void ngx_array_destroy(ngx_array_t *a);//其实只是移动指针并不是真正销毁
void *ngx_array_push(ngx_array_t *a);
void *ngx_array_push_n(ngx_array_t *a, ngx_uint_t n);


static ngx_inline ngx_int_t
ngx_array_init(ngx_array_t *array, ngx_pool_t *pool, ngx_uint_t n, size_t size)//将数组数据区初始化申请n*size大小的内存空间
{
    /*
     * set "array->nelts" before "array->elts", otherwise MSVC thinks
     * that "array->nelts" may be used without having been initialized
     */

    array->nelts = 0;
    array->size = size;
    array->nalloc = n;
    array->pool = pool;

    array->elts = ngx_palloc(pool, n * size);
    if (array->elts == NULL) {
        return NGX_ERROR;
    }

    return NGX_OK;
}
```

![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/src/core/ngx_array_t.jpg)
其中ngx_array_push函数如下
```c
void *
ngx_array_push(ngx_array_t *a)//返回可以push的位置
{
    void        *elt, *new;
    size_t       size;
    ngx_pool_t  *p;

    if (a->nelts == a->nalloc) {

        /* the array is full */

        size = a->size * a->nalloc;

        p = a->pool;

        if ((u_char *) a->elts + size == p->d.last
            && p->d.last + a->size <= p->d.end)//这个数组是内存池的最后一个元素,而且内存池内的剩余空间大于数组一个元素的大小
        {
            /*
             * the array allocation is the last in the pool
             * and there is space for new allocation
             */

            p->d.last += a->size;
            a->nalloc++;

        } else {
            /* allocate a new array */

            new = ngx_palloc(p, 2 * size);//申请一个新的空间,可容纳原来2倍的数据
            if (new == NULL) {
                return NULL;
            }

            ngx_memcpy(new, a->elts, size);//原来的数据并没有销毁
            a->elts = new;
            a->nalloc *= 2;
        }
    }

    elt = (u_char *) a->elts + a->size * a->nelts;
    a->nelts++;

    return elt;
}
```
ngx_queue
---------
```c
typedef struct ngx_queue_s  ngx_queue_t;

struct ngx_queue_s {
    ngx_queue_t  *prev;
    ngx_queue_t  *next;
};


#define ngx_queue_init(q)                                                     \
    (q)->prev = q;                                                            \
    (q)->next = q
```
结构如图
![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/src/core/ngx_queue.jpg)
>nginx的队列操作只对链表指针进行简单的修改指向操作，并不负责节点数据空间的分配。因此，用户在使用nginx队列时，要自己定义数据结构并分配空间，且在其中包含一个ngx_queue_t的指针或者对象，当需要获取队列节点数据时，使用ngx_queue_data宏offsetof(s, m)   (size_t)&(((s *)0)->m) 
offsetof 为结构体内m的偏移量

ngx_list
--------
```c
typedef struct ngx_list_part_s  ngx_list_part_t;

struct ngx_list_part_s {//链表节点结构
    void             *elts;//指向该节点实际的数据区(该数据区中可以存放nalloc个大小为size的元素)  
    ngx_uint_t        nelts;//实际存放的元素个数 
    ngx_list_part_t  *next;//指向下一个节点  
};


typedef struct {//链表头结构  
    ngx_list_part_t  *last;//指向链表最后一个节点(part)  
    ngx_list_part_t   part;//链表头中包含的第一个节点(part) 在链表头内部 
    size_t            size; //每个元素大小  
    ngx_uint_t        nalloc;//链表所含空间个数，即实际分配的小空间的个数  
    ngx_pool_t       *pool;//该链表节点空间在此内存池中分配  
} ngx_list_t;


ngx_list_t *ngx_list_create(ngx_pool_t *pool, ngx_uint_t n, size_t size);//申请链表 初始能包含n个大小为size的数据

static ngx_inline ngx_int_t
ngx_list_init(ngx_list_t *list, ngx_pool_t *pool, ngx_uint_t n, size_t size)
{
    list->part.elts = ngx_palloc(pool, n * size);
    if (list->part.elts == NULL) {
        return NGX_ERROR;
    }

    list->part.nelts = 0;
    list->part.next = NULL;
    list->last = &list->part;
    list->size = size;
    list->nalloc = n;
    list->pool = pool;

    return NGX_OK;
}

```
![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/src/core/ngx_list.jpg)

ngx_hash
--------


ngx_rbtree
----------
首先红黑树的性质
> * 1 节点是红色或黑色。
> * 2 根节点是黑色。
> * 3 每个叶节点（NIL节点，空节点）是黑色的。
> * 4 每个红色节点的两个子节点都是黑色。(从每个叶子到根的所有路径上不能有两个连续的红色节点)
> * 5 从任一节点到其每个叶子的所有路径都包含相同数目的黑色节点。

难点为红黑树的插入和删除


1.红黑树的插入  
因为一般情况下黑色节点的个数是远大于红色节点的数量,所以红黑树默认插入的节点颜色为红色,避免插入需要大概率调整红黑树.
分为以下几种情况.

 (1) 起始为空树.
>此时直接将根指向新节点,并将节点变黑.
 
 (2)新节点的父节点颜色为黑
>直接插入没有影响.

 (3)新节点的父节点颜色为红
  1. 父节点与叔父节点均为红色.  
  此时把父节点和叔父节点的颜色置黑,祖父节点颜色置红.此时祖父节点颜色改变要递归向上
  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_insert1.jpg)  
  2. 父节点为红色,叔父节点为黑色,且新节点为其父节点的左子树.  
  将新节点的父节点置黑,祖父节点置红,然后以祖父节点右旋.
  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_insert2.jpg)  
  3. 父节点为红色,叔父节点为黑色,且新节点为父节点的右子树.  
  以新节点的父节点左旋,则变为2.的情况
  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_insert3.jpg)  
  
  
  当n的父节点为右孩子节点,有对称的3种情况.  
  由于1.是递归向上的最后把根节点置黑.  
  ```c
  void
ngx_rbtree_insert(ngx_rbtree_t *tree, ngx_rbtree_node_t *node)
{
    ngx_rbtree_node_t  **root, *temp, *sentinel;

    /* a binary tree insert */

    root = (ngx_rbtree_node_t **) &tree->root;
    sentinel = tree->sentinel;

    if (*root == sentinel) {//root为nil节点,则添加新的节点,root指向新的节点
        node->parent = NULL;
        node->left = sentinel;
        node->right = sentinel;
        ngx_rbt_black(node);
        *root = node;

        return;
    }

    tree->insert(*root, node, sentinel);

    /* re-balance tree */

    while (node != *root && ngx_rbt_is_red(node->parent)) {//node不是根节点而且node父节点是红色

        if (node->parent == node->parent->parent->left) {//node的父节点是左子树
            temp = node->parent->parent->right;//temp为node的叔父节点
            /*
                node的父节点是左子树,且node的父节点和叔父节点都为红色
                则将node的父节点和叔父节点置黑.node的祖父节点置红
            */

            if (ngx_rbt_is_red(temp)) {
                ngx_rbt_black(node->parent);
                ngx_rbt_black(temp);
                ngx_rbt_red(node->parent->parent);
                node = node->parent->parent;

            }
            /*
                node的父节点是红色而其叔父节点是黑色
                如果node是其父节点的右子树则左旋一次,再右旋一次调整
                如果node是其父节点的左子树则右旋一次
            

            */

             else {
                if (node == node->parent->right) {
                    node = node->parent;
                    ngx_rbtree_left_rotate(root, sentinel, node);
                }

                ngx_rbt_black(node->parent);
                ngx_rbt_red(node->parent->parent);
                ngx_rbtree_right_rotate(root, sentinel, node->parent->parent);
            }

        } else {
            /*
            如果node的父节点是右子树且为红色 node的叔父节点是红色 
            则将node的父节点和叔父节点置黑.node的祖父节点置红
            
            如果node的父节点是右子树且为红色,node的叔父节点是黑色
            如node为左子树则先右旋然后左旋
            如node为右子树则左旋
            */


            temp = node->parent->parent->left;

            if (ngx_rbt_is_red(temp)) {
                ngx_rbt_black(node->parent);
                ngx_rbt_black(temp);
                ngx_rbt_red(node->parent->parent);
                node = node->parent->parent;

            } else {
                if (node == node->parent->left) {
                    node = node->parent;
                    ngx_rbtree_right_rotate(root, sentinel, node);
                }

                ngx_rbt_black(node->parent);
                ngx_rbt_red(node->parent->parent);
                ngx_rbtree_left_rotate(root, sentinel, node->parent->parent);
            }
        }
    }

    ngx_rbt_black(*root);
}
 ```
2.红黑树的删除  
 红黑树的删除符合基本的二叉查找树的删除规则.有待删除结点s,实际删除节点t和删除后占有实际删除节点t位置的节点m.
> 1. 待删除结点s没有子结点，即它是一个叶子结点(非NIL)，此时直接删除,s=t,m=NIL。
> 2. 待删除结点s只有一个子结点，则可以直接删除；如果待删除结点s是根结点，则它的子结点变为根结点；如果待删除结点s不是根结点，则用它的子结点替代它的位置,s=t,m为s(或t)的子节点。
> 3. 待删除结点s有两个子结点，首先找出该结点的后继结点t（即右子树中数值最小的那个结点），然后将两个结点进行交换,并将待删除结点s删除，由于后继结点位置不可能有左子结点，对调后的待删除结点也不会有左子结点，因此要把它删除的操作会落入上面两种情况中。
 
 红黑树的删除主要影响性质4,5,此时分为以下几种情况.
 > 1. 实际删除的节点t颜色为红色.  
 > 直接删除,因为红色节点的删除不会影响到红黑树的性质.删除结束.
 > 2. 实际删除的节点t颜色为黑色  
 >  1 . m为红色节点  
 > 由二叉查找树的删除知,原t位置最多只有右侧子树,此时以m为根的子树黑高减一(性质5破坏),若原t节点位置的父节点为红色,则性质4也破坏.此时将m颜色置黑.则性质4,5都恢复,删除完成.  
 >  2 . m为黑色节点  
 >  此时性质5破坏,为了满足红黑树的性质,把m节点颜色假设为双黑.向上递归的消除.
![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_delete.jpg)
 >  2.1  m的兄弟节点p为黑,且p的左右孩子节点均为黑色  
 >   使p置红,m的双黑色向m的父节点转移.递归向上.  
 >  2.2  m的兄弟节点p为黑色,且p的左孩子为黑右孩子为红.  
 >  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_delete2.jpg)
 >    I的颜色为0,1(红或者黑),此时以I左旋,p变为m的祖父节点,且p为黑色,m双黑色消除,但是p的右孩子黑高由原来的(1,2)(I的颜色0 OR 1)变为1,此时只要把I与P的颜色交换并将p的孩子节点颜色置黑,还原黑高.调节完成.  
 >  2.3 m的兄弟节点p为黑色,p的左右孩子都为红色.  
 >  由2.2注意到即使p的左孩子为红,红黑树的性质也都满足,故也可以使用2.2调整.  
 >  2.4 m的兄弟节点p为黑色,p的左孩子为红,右孩子为黑.  
 >  以p节点右旋 交换p与p左孩子的颜色,此时情况转换成2.2  
 >  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_delete3.jpg)
 >  2.5 m的兄弟节点p为红色节点  
 >  以I节点左旋,因p为红色,I必为黑色,P变为I的父节点,旋转后的P节点的父节点可能颜色为红,故交换I与P的颜色,此时m的兄弟节点必为黑色(是原P节点的左孩子)情况转换为上面的2.2,2.3或者2.4  
 >  ![](https://raw.githubusercontent.com/shykoe/reading_nginx/master/images/rbtree_delete4.jpg)

同样当m为其双亲节点的右孩子的时候也有对称的上述几种情况.
```c
void
ngx_rbtree_delete(ngx_rbtree_t *tree, ngx_rbtree_node_t *node)
{
    ngx_uint_t           red;
    ngx_rbtree_node_t  **root, *sentinel, *subst, *temp, *w;

    /* a binary tree delete */

    root = (ngx_rbtree_node_t **) &tree->root;
    sentinel = tree->sentinel;

    if (node->left == sentinel) {
        temp = node->right;
        subst = node;

    } else if (node->right == sentinel) {
        temp = node->left;
        subst = node;

    } else {
        subst = ngx_rbtree_min(node->right, sentinel);

        if (subst->left != sentinel) {
            temp = subst->left;
        } else {
            temp = subst->right;
        }
    }

    if (subst == *root) {
        *root = temp;
        ngx_rbt_black(temp);

        /* DEBUG stuff */
        node->left = NULL;
        node->right = NULL;
        node->parent = NULL;
        node->key = 0;

        return;
    }

    red = ngx_rbt_is_red(subst);

    if (subst == subst->parent->left) {
        subst->parent->left = temp;

    } else {
        subst->parent->right = temp;
    }

    if (subst == node) {

        temp->parent = subst->parent;

    } else {

        if (subst->parent == node) {
            temp->parent = subst;

        } else {
            temp->parent = subst->parent;
        }

        subst->left = node->left;
        subst->right = node->right;
        subst->parent = node->parent;
        ngx_rbt_copy_color(subst, node);

        if (node == *root) {
            *root = subst;

        } else {
            if (node == node->parent->left) {
                node->parent->left = subst;
            } else {
                node->parent->right = subst;
            }
        }

        if (subst->left != sentinel) {
            subst->left->parent = subst;
        }

        if (subst->right != sentinel) {
            subst->right->parent = subst;
        }
    }

    /* DEBUG stuff */
    node->left = NULL;
    node->right = NULL;
    node->parent = NULL;
    node->key = 0;

    if (red) {//红色直接删除成功
        return;
    }

    /* a delete fixup */

    while (temp != *root && ngx_rbt_is_black(temp)) {

        if (temp == temp->parent->left) {//temp为双黑色
            w = temp->parent->right;//w为temp的兄弟节点

            if (ngx_rbt_is_red(w)) {//w为红色
                ngx_rbt_black(w);
                ngx_rbt_red(temp->parent);
                ngx_rbtree_left_rotate(root, sentinel, temp->parent);
                w = temp->parent->right;
            }

            if (ngx_rbt_is_black(w->left) && ngx_rbt_is_black(w->right)) {
                ngx_rbt_red(w);
                temp = temp->parent;

            } else {
                if (ngx_rbt_is_black(w->right)) {
                    ngx_rbt_black(w->left);
                    ngx_rbt_red(w);
                    ngx_rbtree_right_rotate(root, sentinel, w);
                    w = temp->parent->right;
                }

                ngx_rbt_copy_color(w, temp->parent);
                ngx_rbt_black(temp->parent);
                ngx_rbt_black(w->right);
                ngx_rbtree_left_rotate(root, sentinel, temp->parent);
                temp = *root;
            }

        } else {
            w = temp->parent->left;

            if (ngx_rbt_is_red(w)) {
                ngx_rbt_black(w);
                ngx_rbt_red(temp->parent);
                ngx_rbtree_right_rotate(root, sentinel, temp->parent);
                w = temp->parent->left;
            }

            if (ngx_rbt_is_black(w->left) && ngx_rbt_is_black(w->right)) {
                ngx_rbt_red(w);
                temp = temp->parent;

            } else {
                if (ngx_rbt_is_black(w->left)) {
                    ngx_rbt_black(w->right);
                    ngx_rbt_red(w);
                    ngx_rbtree_left_rotate(root, sentinel, w);
                    w = temp->parent->left;
                }

                ngx_rbt_copy_color(w, temp->parent);
                ngx_rbt_black(temp->parent);
                ngx_rbt_black(w->left);
                ngx_rbtree_right_rotate(root, sentinel, temp->parent);
                temp = *root;
            }
        }
    }

    ngx_rbt_black(temp);
}
```







 
