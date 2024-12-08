def solve(k,n,seeds):
    golden_pounch=[]
    for start in range(0, n, k):
        group = seeds[start:min(start+k,n)]
        if len(group) < k:
            golden_pounch.extend(group)
        else:
            average = sum(group) // len(group)

            if average % 2 == 0:
                golden_pounch.append(average)
    return golden_pounch

def main():
    k=int(input())
    n=int(input())
    seeds = list(map(int,input().split()))

    result = solve(k,n,seeds)
    print(' '.join(map(str,result))+ ' null ')

if __name__ == "__main__":
    main()