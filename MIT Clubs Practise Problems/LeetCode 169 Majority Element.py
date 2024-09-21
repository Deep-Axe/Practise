'''possible apparoached brute forcing, sorting, hash map, random, divide and conquer, bit manipulation, bayes moore voting algorithm'''
#sort
class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        nums.sort()
        return nums[len(nums)//2]

#hash map
class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        n=len(nums)
        hash=defaultdict(int)

        for num in nums:
            hash[num]+=1
        n=n//2
        for key,value in hash.items():
            if value>n:
                return key
            
#Bayes Moore Voting Algorithm
class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        count, present =0,0
        for num in nums:
            if count ==0:
                present=num
            if num == present:
                count+=1
            else:
                count -=1
        return present

''' brute forcing has poor efficiency, random should ideally give soln in o(n), but could theoretially diverge to o(ininity), divide and conquer, bit manipulation to be tried'''