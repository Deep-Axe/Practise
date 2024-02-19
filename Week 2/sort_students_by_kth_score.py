from typing import List
class Solution:
    def sortTheStudents(self, score: List[List[int]], k: int) -> List[List[int]]:
        for j in range(len(score)):
            for i in range(0, len(score) - j - 1):
                if score[i][k] < score[i+1][k]: 
                    score[i], score[i+1] = score[i+1], score[i]

        return score
    
class Solution:
    def sortTheStudents(self, score: List[List[int]], k: int) -> List[List[int]]:
        return sorted(score, key=lambda x: -x[k])
        