from queue import Queue
##black-0 red-1
class Node(object):
	def __init__(self, data = -1, lchild = None, rchild = None, parent = None, color = 1):##default red
		self.data = data
		self.lchild = lchild
		self.rchild = rchild
		self.parent = parent
		self.color = color
	def __str__(self):
		return self.data
class rbtree(object):
	def __init__(self, sentinel):
		self.root = Node(data = 0,color = 0)
		self.sentinel = sentinel
	def insert_value(self,value):
		tmpn = self.root
		while(1):
			p = value > 

def dump_tree(rbtree):
	temp = Queue()
	temp.put(rbtree.root)
	while(not temp.empty()):
		temp_node = temp.get()
		print("data %s color %s" %(temp_node.data if temp_node.data != -1 else 'sentinel', 'red' if temp_node.color == 1 else 'black'))
		if temp_node.data != -1:
			temp.put(temp_node.lchild)
			temp.put(temp_node.rchild)
			

def rbtree_left_rotate(rbtree,Node):
	temp = Node.rchild
	Node.rchild = temp.lchild
	if temp.lchild != rbtree.sentinel:
		temp.lchild.parent = Node
	temp.parent = Node.parent
	if rbtree.root == Node:
		rbtree.root = temp
	elif Node == Node.parent.lchild :
		Node.parent.lchild = temp
	else:
		Node.parent.rchild = temp
	Node.parent = temp
	temp.lchild = Node
def rbtree_right_rotate(rbtree,Node):
	temp = Node.lchild
	Node.lchild = temp.rchild
	if temp.rchild != rbtree.sentinel:
		temp.rchild.parent = Node
	temp.parent = Node.parent
	if rbtree.root == Node:
		rbtree.root = temp
	elif Node == Node.parent.lchild:
		Node.parent.lchild = temp
	else:
		Node.parent.rchild = temp
	Node.parent = temp
	temp.rchild = Node
if __name__ == '__main__':
	sentinel = Node(data = -1)
	root = rbtree(sentinel)
	root.root.lchild = Node(data = 1, lchild = sentinel, rchild = sentinel, parent = root.root)
	rnode = Node(data = 2, lchild = sentinel,rchild = sentinel, parent = root.root)
	root.root.rchild = rnode
	rnode.lchild = Node(data = 3, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
	rnode.rchild = Node(data = 4, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
"""
Node(data = 3, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
Node(data = 4, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
"""