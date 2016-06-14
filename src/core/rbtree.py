class Node(object):
	def __init__(self, data = -1, lchild = None, rchild = None, parent = None, color = ''):
		self.data = data
		self.lchild = lchild
		self.rchild = rchild
		self.parent = parent
		self.color = color
class rbtree(object):
	def __init__(self, root, sentinel):
		self.root = Node(data = 0,color = 'black')
		self.sentinel = sentinel

