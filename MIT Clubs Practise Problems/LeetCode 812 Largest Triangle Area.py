'''try both herons and shoelace'''
class Solution:
    def largestTriangleArea(self, points: List[List[int]]) -> float:
        l,a=len(points),0
        for i in range(l-2):
            for j in range (i+1,l-1):
                for k in range (j+1,l):
                    r=self.shoelace(points[i],points[j],points[k])
                    a=max(a,r)
        return a
    def shoelace(self,x,y,z):
        return abs(x[0]*y[1]+y[0]*z[1]+z[0]*x[1]-(x[0]*z[1]+z[0]*y[1]+y[0]*x[1]))/2
        