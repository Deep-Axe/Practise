#easy
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        hash={}
        for i in range(len(nums)):
            comp=target-nums[i]
            if comp in hash:
                return [i,hash[comp]]
            hash[nums[i]]=i
    ''' given solution is 1 pass hash map
    other possible suboptimal approaches include brute forcing o(n^2) or a 2 pass hash map with o(2n)'''