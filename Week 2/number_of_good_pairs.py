class Solution:
    def numIdenticalPairs(self, nums: List[int]) -> int:
        hash={}
        res=0
        for num in nums:
            if num in hash:
                res+=hash[num]
                hash[num]+=1
            else:
                hash[num]=1
        return res

        