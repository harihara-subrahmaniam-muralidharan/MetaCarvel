import networkx as nx
from collections import deque
from networkx.drawing.nx_agraph import write_dot
import operator


'''
This method validates if separation pair given by SPQR tree is valid source-sink pair for bubble
The algorithm is same as the one in Marygold
'''

def test_pair(G,source,sink,members):

	# if G.has_edge(source,sink) or G.has_edge(sink,source):
	# 	return []

	visited = {}
	visited_nodes = {}
	# visited_nodes = set()
	# visited_nodes.add(source)
	visited_nodes[source] = True
	Q = deque()
	at_sink = False
	for edge in G.out_edges(source):
		Q.appendleft(edge)
		visited[edge] = True

	while not len(Q) == 0:
		#print len(Q)
		go_ahead = True
		curr_edge = Q.pop()
		u = curr_edge[0]
		v = curr_edge[1]
		if v not in members:
			return False
		visited_nodes[v] = True
		if v == sink:
			at_sink = True
			continue
		for edge in G.in_edges(v):
			if edge not in visited:
				go_ahead = False
				break

		if go_ahead:
			visited[edge] = True
			for edge in G.out_edges(v):
				if edge not in visited:
					Q.appendleft(edge)
					visited[edge] = True
	
	
	
	if at_sink:
		return True
	else:
		return False


'''
This method finds out all shortest paths between source and sink in subg.
It returns a list of paths with first path being a heaviest path 
'''
def get_all_shortest_paths(subg, source, sink):
	all_paths = nx.all_simple_paths(subg,source,sink)
	id2path = {}
	id2weight = {}
	id = 1
	for path in all_paths:
		id2path[id] = path
		
		wt = 0
		for i in xrange(0,len(path)-1):
			wt += subg[path[i]][path[i+1]]['bsize']

		id2weight[id] = wt
		id += 1

	sorted_path = sorted(id2weight, key=lambda k: id2weight[k], reverse=True)
	ret = []
	for key in sorted_path:
		ret.append(id2path[key])

	return ret



'''
This method takes a graph and makes it acyclic by removing lowest cost edge in a cycle
'''

def make_acyclic(G):
	G_copy = G.copy()
	F = []
	original_G = G.copy()
	while not nx.is_directed_acyclic_graph(G_copy):
		#iterate through cycles in G
		
		for cycle in nx.simple_cycles(G_copy):
			min_weight = 100000
			min_u = 0
			min_v = 0
			#Find minimum weight edge in the cycle, weight
			#here is bundle size
			#TODO: start with smallest cycle by sorting
			#print G.edges(data=True)
			for i in xrange(0,len(cycle)-1):
				u = cycle[i]
				v = cycle[i+1]
				if G[u][v]['bsize'] < min_weight:	
					min_weight = G[u][v]['bsize']
					min_u = u
					min_v = v
			if G[cycle[- 1]][cycle[0]]['bsize'] < min_weight:
				min_weight = G[cycle[-1]][cycle[0]]['bsize']
				min_u = cycle[-1]
				min_v = cycle[0]

			#reduce the edge weights by min_weight and remove the edge if its weight is 0
			if min_weight != 100000:
				for i in xrange(0,len(cycle)-1):
					u = cycle[i]
					v = cycle[i+1]
					G[u][v]['bsize'] -= min_weight
				
				G[cycle[-1]][cycle[0]]['bsize'] -= min_weight
				G.remove_edge(min_u,min_v)
				F.append((min_u,min_v,original_G.get_edge_data(min_u,min_v)))
				G_copy = G.copy()
				break

	#Now try adding edges from F to G, TODO do in non-increasing order

		if len(G.edges()) == 0:
			continue
		# if len(G.nodes()) == 0:
		# 	continue
		for edge in F:
			u = edge[0]
			v = edge[1]
			G.add_edge(u,v,edge[2])
			if not nx.is_directed_acyclic_graph(G):
				G.remove_edge(u,v)

	return G


'''
Helper to no_of_paths method
'''
def no_of_paths_helper(subg,source,sink,dp):
	# print "source = " + source
	# print "sink = " + sink
	if source == sink:
		return 1
	if dp[source] != -1:
		return dp[source]
	ret = 0
	for u,v in subg.out_edges(source):
		#print u,v
		ret += no_of_paths_helper(subg,v,sink,dp)
	dp[source] = ret
	return ret

'''
This method takes a DAG as input with source and sink and outputs number of paths
between source and sink
'''
def no_of_paths(subg,source,sink):
	#subg = nx.topological_sort(subg)
	dp = {}
	dp[source] = -1
	dp[sink] = -1
	for node in subg.nodes():
		dp[node] = -1
	return  no_of_paths_helper(subg,source,sink,dp)

def main():

	G = nx.read_gml("shakya_oriented.gml")
	#G = nx.read_gml("small.gml")
	nx.write_gexf(G,'original.gexf')
	pairmap = {}
	pair_list = []
	with open('shakya_bicomp','r') as f:
		for line in f:
			attrs = line.split()
			if attrs[0] <= attrs[1]:
				key = attrs[0] +'$'+ attrs[1]
			else:
				key = attrs[1] +'$'+ attrs[0]
			pairmap[key] = attrs[2:]
			pair_list.append(key)

	validated = {}
	contig2id = {}
	cnt = 0
	write_dot(G,'graph.dot')

	# for key in pairmap:
	# 	print len(pairmap[key])

	in_bubble = {}
	valid_source_sink = []
	all_bubble_paths = {} #stores all heaviest paths in bubble
	source_and_sinks = {}
	'''
	Here, first validate each source sink pair. To do this, sort them with largest number of nodes in the
	biconnected component.
	'''
	#pair_list = sorted(pairmap, key=lambda k: len(pairmap[k]), reverse=True)

	# for key in pair_list:
	# 	print pairmap[key]

	comp_to_id = {}
	id_to_comp = {}
	comp_to_pair = {}
	id_to_longest_path = {}
	comp2pairs = {}
	prev_comp = ''
	id = 1
	for key in pair_list:
		comp = pairmap[key]
		if comp[0] == prev_comp:
			continue

		comp_to_id[comp[0]] = id
		comp2pairs[id] = []
		id_to_comp[id] = comp
		comp_to_pair[id] = []
		id_to_longest_path[id] = -1
		id += 1
		prev_comp = comp[0]

	for key in pair_list:
		c = pairmap[key][0]
		comp_id = comp_to_id[c]
		comp_to_pair[comp_id].append(key)

	valid_comps = {}

	for key in pair_list:
		contigs = key.split('$')
		'''
		First find the subgraph of bicomponent. Check if current source sink pair is longer that previously
		validated source sink pair. If yes then only validate current source sink pair.
		'''
		subg = G.subgraph(pairmap[key])
		comp_id = pairmap[key][0]
		comp_id = comp_to_id[comp_id]
		res = test_pair(G,contigs[0],contigs[1],pairmap[key])
		
		if res:
			cnt += 1
			validated[contigs[0]] = 1
			source_and_sinks[contigs[0]] = 1
			source_and_sinks[contigs[1]] = 1
			validated[contigs[1]] = 1
			comp = []
			for contig in pairmap[key]:
				in_bubble[contig] = 1
				validated[contig] = 1
				comp.append(contig)

			subg = G.subgraph(comp)
			valid_comps[comp_id] = 1
			

			
	source = {}
	sink = {}
	source_sink_to_comp = {}
	print len(valid_comps)
	cnt = 0
	for key in valid_comps:
		pairs = comp_to_pair[key]
		#print "Length of pairs = " + str(len(pairs))
		subg = G.subgraph(id_to_comp[key])
		if not nx.is_directed_acyclic_graph(subg):
			subg = make_acyclic(subg)
		if nx.is_directed_acyclic_graph(subg):

			#print subg.nodes()
			max_path = 0
			max_pair = -1
			#print pairs
			for pair in pairs:
				#print pair
				pair1 = pair.split('$')
				no_paths = no_of_paths(subg,pair1[0],pair1[1])
				if no_paths > max_path:
					max_path = no_paths
					max_pair = pair

			if max_pair != -1:
				print "max_path = " + str(max_path)
				print "max_pair = " + str(max_pair)
				cnt += 1
				valid_source_sink.append(max_pair)
				source[max_pair[0]] = 1
				sink[max_pair[1]] = 1
				source_sink_to_comp[max_pair[0]] = key
				source_sink_to_comp[max_pair[1]] = key
				for contig in id_to_comp[key]:
					in_bubble[contig] = 1
					validated[contig] = 1
		# else:
		# 	subg = make_acyclic

	print cnt

	'''
	Here, find now the new graph by collapsing bubbles
	'''

	G_new = nx.DiGraph()
	colmap = {}
	typemap = {}
	for key in valid_comps:
		G.add_node(str(key))
	for u,v,data in G.edges(data=True):
		if u not in validated and v not in validated:
			G_new.add_edge(u,v,data)

	for node in G.nodes():
		for each in source:
			if G.has_edge(node,each):
				G_new.add_edge(node,source_sink_to_comp[each])

		for each in sink:
			if G.has_edge(each,node):
				G_new.add_edge(source_sink_to_comp[each],node)


	'''
	Output the simplified Graph
	'''
	# for node in G_new.nodes(data=True):
	# 	#print node
	# 	m = node[1]
	# 	node[1]['color'] = colmap[node[0]]
	#nx.set_node_attribute(G_new,'color',colmap)
	print len(G_new.nodes())
	print len(G_new.edges())
	nx.write_gexf(G_new,'simplified.gexf')
	write_dot(G_new,'simplified.dot')

	'''
	Make the new simplified graph undirected
	'''
	#G_new = G_new.to_undirected()

	# G_reduced = nx.DiGraph()

	# for subg in nx.weakly_connected_component_subgraphs(G_new):
	# 	subg = transitive_reduction(subg)
	# 	for u,v in subg.edges():
	# 		G_reduced.add_edge(u,v)

	# nx.write_gexf(G_reduced,'t_reduced.gexf')

if __name__ == '__main__':
	main()
