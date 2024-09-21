#greedy

class Solution:
    def maxSatisfaction(self, satisfaction: List[int]) -> int:
        satisfaction.sort()
        max_satisfaction = 0
        suffix_sum = 0
        for i in range(len(satisfaction) - 1, -1, -1):
            if suffix_sum + satisfaction[i] > 0:
                suffix_sum += satisfaction[i]
                max_satisfaction += suffix_sum
            else:
                break  
        return max_satisfaction
    
# #top down dp
from typing import List
class Solution:
    def findMaxSatisfaction(self,satisfaction,memo,index,time):

        if index == len(satisfaction):
            return 0

        if memo[index][time] != -1:
            return memo [index][time]
        
        memo[index][time]=max(satisfaction[index]*time+self.findMaxSatisfaction(satisfaction,memo,index+1,time+1),
        self.findMaxSatisfaction(satisfaction, memo, index+1,time))

        return memo[index][time]

    def maxSatisfaction(self, satisfaction: List[int]) -> int:
       satisfaction.sort()

       memo = [[-1 for _ in range(len(satisfaction)+1)] for _ in range(len(satisfaction)+1)]
       
       return self.findMaxSatisfaction(satisfaction,memo,0,1)
  
#top down dp but more pythonic
from functools import lru_cache
class Solution:
    
    def maxSatisfaction(self, satisfaction: List[int]) -> int:
       satisfaction.sort()
       @lru_cache(maxsize=None)

       def findMaxSatisfaction(index,time):
        if index==len(satisfaction):
            return 0

        return max(satisfaction[index] * time + findMaxSatisfaction(index + 1, time + 1), 
                        findMaxSatisfaction(index + 1, time))

