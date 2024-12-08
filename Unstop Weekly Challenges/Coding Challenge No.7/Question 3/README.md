# **Question 3** 

In a quiet village, a wise elder named Elora tasked the young villagers with an unusual challenge to test their teamwork and mathematical skills. Here's the challenge:\
The villagers were divided into groups of k, where k is a number chosen at random. Each group had to calculate the average number of seeds in the apples they get. However, the task had an odd twist:\
    1. If the average number of seeds per group was an even number, they would place the average into a golden pouch(linked list) for the village's ceremonial tree planting.\
    2. If the average was an odd number, the seeds were discarded, and the group moved on.\
    3. If there were fewer apples left than the group size k, they were to simply collect all the remaining apples and add their seeds to the pouch as they were, without calculating any average.\
Can you determine the final list (linked list) of seeds in the golden pouch based on this challenge?\
***<ins>Note</ins>:*** To add more structure to the challenge, the groups were required to move in a straight line. This meant the first group would take the first k apples, complete their task, and place their result in the pouch before the second group started with the next k apples, and so on.\
***<ins>Note</ins>:*** You have to take the floor of average\

***<ins>Input Format</ins>:***\
The first line contains an integer K, the group size.\
The second line contains an integer N the number of apples.\
The third line contains N space separated integers, the number of seeds in each apple.\
***<ins>Output Format</ins>:***\
Print the linked list of seeds collected in the golden pouch. Each node in the linked list represents a seed value, with the last node pointing to null.\
Don't print any trailing space after the "null".\

### Sample Testcase #0

***<ins>Testcase Input</ins>:***\
3\
10\
2 4 6 8 10 3 5 7 9 11\
***<ins>Testcase Output</ins>:***\
4 11 null\
***<ins>Explanation</ins>:***\
The groups are formed as:\
<ins>Group 1</ins>: [2, 4, 6] (average is 4, even, so added to the pouch)\
<ins>Group 2</ins>: [8, 10, 3] (average is 7, odd, so discarded)\
<ins>Group 3</ins>: [5, 7, 9] (average is 7, odd, so discarded)\
<ins>Group 4</ins>: [11] (less than k, so all seeds are collected without averaging)\
The seeds in the groups with even averages (Group 1) and the last group (Group 4) are added to the golden pouch.\
The output will be: 4 11 null\

### Sample Testcase #1
***<ins>Testcase Input</ins>:***\
2\
5\
1 2 3 4 5\
***<ins>Testcase Output</ins>:***\
5 null\
***<ins>Explanation</ins>:***\
The groups are formed as:\
<ins>Group 1</ins>: [1, 2] (average is 1, odd, so discarded)\
<ins>Group 2</ins>: [3, 4] (average is 3, odd, so discarded)\
<ins>Group 3</ins>: [5] (less than k, so all seeds are collected without averaging)\
The result is that the seeds in the last group (5) are added to the golden pouch. The output will be: 5 null\
