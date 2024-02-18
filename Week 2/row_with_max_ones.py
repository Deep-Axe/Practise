class Solution:
    def rowAndMaximumOnes(self, mat: List[List[int]]) -> List[int]:
        max_ones,index=0,0
        for i in range(len(mat)):
            ones=mat[i].count(1)
            if ones>max_ones:
                max_ones=ones
                index=i
        return [index,max_ones]
   