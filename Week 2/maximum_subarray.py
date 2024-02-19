from typing import List

#kadanes algorithm
class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        cur_sum=max_sum=nums[0]
        for num in nums[1:]:
            cur_sum=max(num,cur_sum+num)
            max_sum=max(max_sum,cur_sum)
        return max_sum
    
#brute force
'''exceeds time limit on leetcode'''
class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        max_sum = float('-inf')
        for i in range(len(nums)):
          current_sum = 0
          for j in range(i, len(nums)):
            current_sum += nums[j]
            max_sum = max(max_sum, current_sum)
        return max_sum
    
#divide and conquer
class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        return self.divide_and_conquer(nums, 0, len(nums) - 1)

    def cross_sum(self, nums, left, right, mid):
        if left == right:
            return nums[left]

        left_subsum = float('-inf')
        curr_sum = 0
        for i in range(mid, left - 1, -1):
            curr_sum += nums[i]
            left_subsum = max(left_subsum, curr_sum)

        right_subsum = float('-inf')
        curr_sum = 0
        for i in range(mid + 1, right + 1):
            curr_sum += nums[i]
            right_subsum = max(right_subsum, curr_sum)

        return left_subsum + right_subsum

    def divide_and_conquer(self, nums, left, right):
        if left == right:
            return nums[left]

        mid = (left + right) // 2

        left_sum = self.divide_and_conquer(nums, left, mid)
        right_sum = self.divide_and_conquer(nums, mid + 1, right)
        cross_sum = self.cross_sum(nums, left, right, mid)

        return max(left_sum, right_sum, cross_sum)
    
