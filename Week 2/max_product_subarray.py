class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        global_max=old_max=old_min=nums[0]
        for num in nums[1:]:
            local_min=min(old_max*num,old_min*num,num)
            local_max=max(old_max*num,old_min*num,num)
            global_max=max(global_max,local_max)
            old_max=local_max
            old_min=local_min
        return global_max
            
        