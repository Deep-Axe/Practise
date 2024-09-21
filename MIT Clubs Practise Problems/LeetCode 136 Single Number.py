class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        all_xor=0
        for i in nums:
            all_xor^=i
        return all_xor
        
''' xor gives positive for dissimalr inputs'''