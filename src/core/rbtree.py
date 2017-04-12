from queue import Queue
import pdb
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
		self.root = Node(data = 0, lchild = sentinel, rchild = sentinel, parent = sentinel, color = 0)
		self.sentinel = sentinel

	def insert_value(self,value):
		p = self.root
		while True:
			tmpn = p
			p =  p.rchild if value > p.data else p.lchild			
			if p == self.sentinel:
				break
		newnode = Node(data = value, lchild = self.sentinel, rchild = self.sentinel, parent = tmpn )
		if value > tmpn.data:
			tmpn.rchild = newnode
		else:
			tmpn.lchild = newnode
		p = newnode
		#balance tree
		while(p != self.root and is_red(p.parent)):
			if p.parent == p.parent.parent.lchild:
				tmpn = p.parent.parent.rchild
				if(is_red(tmpn)):
					black(tmpn)
					black(p.parent)
					red(p.parent.parent)
					p = p.parent.parent
				else:
					if p == p.parent.rchild:
						p = p.parent
						rbtree_left_rotate(self,p)
					black(p.parent)
					red(p.parent.parent)
					rbtree_right_rotate(self,p.parent.parent)
			else:
				tmpn = p.parent.parent.lchild
				if(is_red(tmpn)):
					black(tmpn)
					black(p.parent)
					red(p.parent.parent)
					p = p.parent.parent
				else:
					if p == p.parent.lchild:
						p = p.parent
						rbtree_right_rotate(self,p)
					black(p.parent)
					red(p.parent.parent)
					rbtree_left_rotate(self,p.parent.parent) 
		black(self.root)
	def delete_node(self, node):
		"""
		binary tree delete
		"""
		if node.lchild == self.sentinel:
			temp = node.rchild
			subst = node
		elif node.rchild == self.sentinel:
			temp = node.lchild
			subst = node
		else:
			subst = tree_min(node.rchild, self.sentinel)
			temp = subst.rchild

		if subst == self.root:
			self.root = temp
			black(temp)
			node.parent = None
			node.rchild = lchild = None
			return
		flag_red = is_red(subst)
		if subst == subst.parent.lchild:
			subst.parent.lchild = temp
		else:
			subst.parent.rchild = temp
		if subst == node:
			temp.parent = subst.parent
		else:
			if subst.parent == node:
				temp.parent = subst
			else:
				temp.parent = subst.parent
			subst.rchild = node.rchild
			subst.lchild = node.lchild
			subst.parent = node.parent
			subst.color = node.color
			if node == self.root:
				self.root = subst
			else:
				if node == node.parent.lchild:
					node.parent.lchild = subst
				else:
					node.parent.rchild = subst
			if subst.lchild != self.sentinel:
				subst.lchild.parent = subst
			if subst.rchild != self.sentinel:
				subst.rchild.parent = subst
		node.lchild = None
		node.rchild = None
		node.parent = None
		node.data = 0
		if flag_red:
			return
		"""
		balance rbtree
		"""
		while(temp != self.root and is_black(temp)):
			
			if temp == temp.parent.lchild:
				p = temp.parent.rchild
				if is_red(p):
					rbtree_left_rotate(self,temp.parent)
					black(p)
					red(temp.parent)
					p = temp.parent.rchild
				if is_black(p.lchild) and is_black(p.rchild):
					red(p)
					temp = temp.parent
				else:
					if is_black(p.rchild):
						black(p.lchild)
						rbtree_right_rotate(self,p)
						red(p)
						p = temp.parent.rchild
					rbtree_left_rotate(self,temp.parent)
					p.color = temp.parent.color
					black(temp.parent)
					black(p.rchild)
					temp = self.root
			else:
				p = temp.parent.lchild
				if is_red(p):
					rbtree_right_rotate(self,temp.parent)
					black(p)
					red(temp.parent)
					p = temp.parent.lchild
				if is_black(p.lchild) and is_black(p.rchild):
					red(p)
					temp = temp.parent
				else:
					if is_black(p.lchild):
						black(p.rchild)
						rbtree_left_rotate(self,p)
						red(p)
						p = temp.parent.lchild
					rbtree_right_rotate(self,temp.parent)
					p.color = temp.parent.color
					black(temp.parent)
					black(p.lchild)
					temp = self.root
		black(temp)			








def tree_min(node, sentinel):
	while(node.lchild != sentinel):
		node = node.lchild
	return node
def red(node):
	node.color = 1
def black(node):
	node.color = 0
def is_red(node):
	return node.color == 1
def is_black(node):
	return node.color == 0

def dump_tree(rbtree):
	temp = Queue()
	temp.put(rbtree.root)
	while(not temp.empty()):
		temp_node = temp.get()
		print("data %s color %s" %(temp_node.data if temp_node.data != -999 else 'sentinel', 'red' if temp_node.color == 1 else 'black'))
		if temp_node.data != -999:
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
	sentinel = Node(data = -999,color = 0)
	root = rbtree(sentinel)
	for x in range(1,10):
		root.insert_value(x)

"""	
	root.root.lchild = Node(data = 1, lchild = sentinel, rchild = sentinel, parent = root.root)
	rnode = Node(data = 2, lchild = sentinel,rchild = sentinel, parent = root.root)
	root.root.rchild = rnode
	rnode.lchild = Node(data = 3, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
	rnode.rchild = Node(data = 4, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)

Node(data = 3, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
Node(data = 4, lchild = sentinel, rchild = sentinel, parent = rnode, color = 0)
"""