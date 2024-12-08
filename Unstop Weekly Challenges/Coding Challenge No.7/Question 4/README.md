# **Question 4** 

In a peaceful village, the wise sage decided to introduce a new challenge at the annual harvest festival. He handed out numbered stones to the villagers and told them the task: find pairs of stones such that each numbers were divisible by either of two special numbers, N and M.
The villagers quickly grouped the stones, checking which ones met the criteria. They worked together, carefully pairing up the stones that were divisible by either N or M, making sure no pair was repeated and a pair must contain different stone.\
By the end of the day, they had discovered several unique pairs, and the sage was pleased with their effort and the count they got.\

***<ins>Input Format</ins>:***\
The first line contains three space-separated integers P, N, and M, where P is the number of stones in the village and N and M are the special numbers used to identify lucky stones.\
The second line contains P space-separated integers, each representing the number on a stone.\
***<ins>Output Format</ins>:***\
Output a single integer representing the number of pairs the villagers got at the end of the day.\


### Sample Testcase #0

***<ins>Testcase Input</ins>:***\
5 2 3\
6 9 12 15 18\
***<ins>Testcase Output</ins>:***\
10\
***<ins>Explanation</ins>:***\
The valid pairs of stone, where the each number is divisible by either 2 or 3 are (6,9); (6,12); (6,15); (6,18); (9,12); (9,15); (9,18); (12,15); (12,18) and (15,18). The count is 10.\

### Sample Testcase #1
***<ins>Testcase Input</ins>:***\
4 4 4\
2 5 5 8\
***<ins>Testcase Output</ins>:***\
0\
***<ins>Explanation</ins>:***\
No valid pair found.