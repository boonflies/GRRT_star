"""

Path planning Sample Code with RRT*

author: Atsushi Sakai(@Atsushi_twi)

"""

import math
import os
import sys

import matplotlib.pyplot as plt

import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../RRT/")

try:
    from rrt import RRT
except ImportError:
    raise

show_animation = True


class RRTStar(RRT):
    """
    Class for RRT Star planning
    """

    class Node(RRT.Node):
        def __init__(self, x, y):
            super().__init__(x, y)
            self.cost = 0.0

    def __init__(self,
                 start,
                 goal,
                 obstacle_list,
                 rand_area,
                 expand_dis=30.0,
                 path_resolution=1.0,
                 goal_sample_rate=20,
                 max_iter=1000,
                 connect_circle_dist=50.0,
                 search_until_max_iter=False):
        """
        Setting Parameter

        start:Start Position [x,y]
        goal:Goal Position [x,y]
        obstacleList:obstacle Positions [[x,y,size],...]
        randArea:Random Sampling Area [min,max]

        """
        super().__init__(start, goal, obstacle_list, rand_area, expand_dis,
                         path_resolution, goal_sample_rate, max_iter)
        self.connect_circle_dist = connect_circle_dist
        self.goal_node = self.Node(goal[0], goal[1])
        self.search_until_max_iter = search_until_max_iter
        self.end = self.Node(goal[0], goal[1])
        self.start_time = 0
        ct_excel = 2
        self.iter_count = 0

    def planning(self, animation=True):
        """
        rrt star path planning

        animation: flag for animation on or off .
        """
        
        self.node_list = [self.start]
 
        for i in range(self.max_iter):
            print("Iter:", i, ", number of nodes:", len(self.node_list))
            self.iter_count = i
            rnd = self.get_random_node()
            rnd1 = self.get_random_node()
            rnd2 = self.get_random_node()
            rnd3 = self.get_random_node()
            rnd4 = self.get_random_node()
            to_node = self.goal_node
            dist1, _ = self.calc_distance_and_angle(rnd1, to_node)
            dist2, _ = self.calc_distance_and_angle(rnd2, to_node)
            dist3, _ = self.calc_distance_and_angle(rnd3, to_node)
            dist4, _ = self.calc_distance_and_angle(rnd4, to_node)
	    
            if (dist1 < dist2 and dist1 < dist3 and dist1 < dist4):
               rnd = rnd1

            if (dist2 < dist1 and dist2 < dist3 and dist2 < dist4):
               rnd = rnd2

            if (dist3 < dist1 and dist3 < dist2 and dist3 < dist4):
               rnd = rnd3

            if (dist4 < dist1 and dist4 < dist2 and dist4 < dist3):
               rnd = rnd4

            nearest_ind = self.get_nearest_node_index(self.node_list, rnd)
            new_node = self.steer(self.node_list[nearest_ind], rnd,
                                  self.expand_dis)
            near_node = self.node_list[nearest_ind]
            new_node.cost = near_node.cost + \
                math.hypot(new_node.x-near_node.x,
                           new_node.y-near_node.y)

            if self.check_collision(new_node, self.obstacle_list):
                near_inds = self.find_near_nodes(new_node)
                node_with_updated_parent = self.choose_parent(
                    new_node, near_inds)
                if node_with_updated_parent:
                    self.rewire(node_with_updated_parent, near_inds)
                    self.node_list.append(node_with_updated_parent)
                else:
                    self.node_list.append(new_node)

            if animation:
                self.draw_graph(rnd)

            if ((not self.search_until_max_iter)
                    and new_node):  # if reaches goal
                last_index = self.search_best_goal_node()
                if last_index is not None:
                    return self.generate_final_course_star(last_index)

        print("reached max iteration")
        
        last_index = self.search_best_goal_node()
        if last_index is not None:
            return self.generate_final_course_star(last_index)

        return None

    def choose_parent(self, new_node, near_inds):
        """
        Computes the cheapest point to new_node contained in the list
        near_inds and set such a node as the parent of new_node.
            Arguments:
            --------
                new_node, Node
                    randomly generated node with a path from its neared point
                    There are not coalitions between this node and th tree.
                near_inds: list
                    Indices of indices of the nodes what are near to new_node

            Returns.
            ------
                Node, a copy of new_node
        """
        if not near_inds:
            return None

        # search nearest cost in near_inds
        costs = []
        for i in near_inds:
            near_node = self.node_list[i]
            t_node = self.steer(near_node, new_node)
            if t_node and self.check_collision(t_node, self.obstacle_list):
                costs.append(self.calc_new_cost(near_node, new_node))
            else:
                costs.append(float("inf"))  # the cost of collision node
        min_cost = min(costs)

        if min_cost == float("inf"):
            print("There is no good path.(min_cost is inf)")
            return None

        min_ind = near_inds[costs.index(min_cost)]
        new_node = self.steer(self.node_list[min_ind], new_node)
        new_node.cost = min_cost

        return new_node

    def search_best_goal_node(self):
        dist_to_goal_list = [
            self.calc_dist_to_goal(n.x, n.y) for n in self.node_list
        ]
        goal_inds = [
            dist_to_goal_list.index(i) for i in dist_to_goal_list
            if i <= self.expand_dis
        ]

        safe_goal_inds = []
        for goal_ind in goal_inds:
            t_node = self.steer(self.node_list[goal_ind], self.goal_node)
            if self.check_collision(t_node, self.obstacle_list):
                safe_goal_inds.append(goal_ind)

        if not safe_goal_inds:
            return None

        min_cost = min([self.node_list[i].cost for i in safe_goal_inds])
        for i in safe_goal_inds:
            if self.node_list[i].cost == min_cost:
                return i

        return None

    def find_near_nodes(self, new_node):
        """
        1) defines a ball centered on new_node
        2) Returns all nodes of the three that are inside this ball
            Arguments:
            ---------
                new_node: Node
                    new randomly generated node, without collisions between
                    its nearest node
            Returns:
            -------
                list
                    List with the indices of the nodes inside the ball of
                    radius r
        """
        nnode = len(self.node_list) + 1
        r = self.connect_circle_dist * math.sqrt((math.log(nnode) / nnode))
        # if expand_dist exists, search vertices in a range no more than
        # expand_dist
        if hasattr(self, 'expand_dis'):
            r = min(r, self.expand_dis)
        dist_list = [(node.x - new_node.x)**2 + (node.y - new_node.y)**2
                     for node in self.node_list]
        near_inds = [dist_list.index(i) for i in dist_list if i <= r**2]
        return near_inds

    def rewire(self, new_node, near_inds):
        """
            For each node in near_inds, this will check if it is cheaper to
            arrive to them from new_node.
            In such a case, this will re-assign the parent of the nodes in
            near_inds to new_node.
            Parameters:
            ----------
                new_node, Node
                    Node randomly added which can be joined to the tree

                near_inds, list of uints
                    A list of indices of the self.new_node which contains
                    nodes within a circle of a given radius.
            Remark: parent is designated in choose_parent.

        """
        for i in near_inds:
            near_node = self.node_list[i]
            edge_node = self.steer(new_node, near_node)
            if not edge_node:
                continue
            edge_node.cost = self.calc_new_cost(new_node, near_node)

            no_collision = self.check_collision(edge_node, self.obstacle_list)
            improved_cost = near_node.cost > edge_node.cost

            if no_collision and improved_cost:
                near_node.x = edge_node.x
                near_node.y = edge_node.y
                near_node.cost = edge_node.cost
                near_node.path_x = edge_node.path_x
                near_node.path_y = edge_node.path_y
                near_node.parent = edge_node.parent
                self.propagate_cost_to_leaves(new_node)

    def calc_new_cost(self, from_node, to_node):
        d, _ = self.calc_distance_and_angle(from_node, to_node)
        return from_node.cost + d

    def propagate_cost_to_leaves(self, parent_node):

        for node in self.node_list:
            if node.parent == parent_node:
                node.cost = self.calc_new_cost(parent_node, node)
                self.propagate_cost_to_leaves(node)
    
    def generate_final_course_star(self, goal_ind):
        path = [[self.end.x, self.end.y]]
        end_node = self.Node(self.end.x, self.end.y)
        node = self.node_list[goal_ind]
        distance, theta = self.calc_distance_and_angle(node, end_node)
        distance =  distance + node.dist_to_start
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([node.x, node.y])

        print("The final course\n")
        print("Distance of the path:", distance)
        print("Number of nodes in the path",len(path))
        print("Number of nodes in the tree",(len(self.node_list)))
        print("Number of random nodes generated",self.random_node_count)
        print("Number of Collision Checks",self.collision_check_count)
        print("Time taken for collision check",self.collision_check_time)  

        print("ct_excel",ct_excel)
        sheet1.write(ct_excel, 1, distance) 
        sheet1.write(ct_excel, 2, len(path)) 
        sheet1.write(ct_excel, 3, (len(self.node_list)))
        sheet1.write(ct_excel, 4, self.random_node_count) 
        sheet1.write(ct_excel, 5, self.collision_check_count) 
        sheet1.write(ct_excel, 6, self.collision_check_time)      
        sheet1.write(ct_excel, 7, self.iter_count) 
        sheet1.write(ct_excel, 8, (time.time() - self.start_time)) 
        
        # for index in range(len(path)):
        #     print(path[index])

        return path

def main():
   # print("Start " + __file__)    
    global ct_excel
    ct_excel = 1
    print(range(NUM_OF_TRIALS))
    for iteration in range(NUM_OF_TRIALS): 
       print("iteration")
       print(iteration)
      
       # ====Search Path with RRT====
       obstacle_list = [
           (5, 5, 1),
           (3, 6, 2),
           (3, 8, 2),
           (3, 10, 2),
           (7, 5, 2),
           (9, 5, 2),
           (8, 10, 1),
           (6, 12, 1),
       ]  # [x,y,size(radius)]

       # Set Initial parameters
       rrt_star = RRTStar(
           start=[0, 0],
           goal=[6, 10],
           rand_area=[-2, 15],
           obstacle_list=obstacle_list,
           expand_dis=1)
       rrt_star.start_time = time.time()  
       path = rrt_star.planning(animation=show_animation)

       if path is None:
           print("Cannot find path")
       else:
           print("found path!!")
           ct_excel = ct_excel + 1	

           # Draw final path
           #if show_animation:
            #   rrt_star.draw_graph()
             #  plt.plot([x for (x, y) in path], [y for (x, y) in path], 'r--')
              # plt.grid(True)
#       plt.show()


if __name__ == '__main__':

    NUM_OF_TRIALS = 50
    import xlwt 
    from xlwt import Workbook 
  
# Workbook is created 
    wb = Workbook() 
  
# add_sheet is used to create sheet. 
    sheet1 = wb.add_sheet('Sheet 1', cell_overwrite_ok=True) 
    sheet1.write(0, 1, 'Distance of the path') 
    sheet1.write(0, 2, 'Number of nodes in the path') 
    sheet1.write(0, 3, 'Number of nodes in the tree') 
    sheet1.write(0, 4, 'Number of random nodes generated') 
    sheet1.write(0, 5, 'Number of Collision Checks') 
    sheet1.write(0, 6, 'Time taken for collision check')   
    sheet1.write(0, 7, 'Iteration')   
    sheet1.write(0, 8, 'Time taken for planning')   

    
    main()
    

    wb.save('RRT_star.xls')
