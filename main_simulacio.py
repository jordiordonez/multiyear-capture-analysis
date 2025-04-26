from modules.simulacio import simular_6_anys

if __name__ == '__main__':
    inicial = 'sorteig.csv'
    captures_per_any = 150
    simular_6_anys(inicial, captures_per_any, years=6, seed=42)
