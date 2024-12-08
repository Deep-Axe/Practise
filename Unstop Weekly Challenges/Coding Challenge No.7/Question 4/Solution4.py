def count(P,N,M,numbers):
  pairs = 0
  for i in range(len(numbers)):
    for j in range((i+1),len(numbers)):  
      if (numbers[i] % N == 0 or numbers[i] % M == 0):
        if (numbers[j] % M == 0 or numbers[j] % N == 0):
          pairs += 1
  return (pairs)

def main():
  P, N, M = map(int,input().split())
  numbers = list(map(int,input().split()))

  result = count(P,N,M,numbers)
  print(result)

if __name__ == "__main__":
  main()

'''note: explicitly checking num[i] != num[j] led to failing of few test cases'''