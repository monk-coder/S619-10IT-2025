# main.py
# TODO:TRY EXCEPT TO EVERYTHING!!!!! (eg data validation in Person (salary and expenses))
from person import Person
from simulation import Simulation
import json
from pathlib import Path

def main():
    print("=== Bob and Alice Life Simulation ===")

 # вывел проверку в отдельную функцию, чтобы изолировать и переиспользовать логику проверок
 # (все как гласят великие праила на notion 10it :) )   

    def read_int(prompt, min_value=None, max_value=None):
        while True:
            try:
                raw = input(prompt)
                value = int(raw)
                if min_value is not None and value < min_value:
                    print(f"Value must be >= {min_value}. Try again.")
                    continue
                if max_value is not None and value > max_value:
                    print(f"Value must be <= {max_value}. Try again.")
                    continue
                return value
            except ValueError:
                print("Please enter a valid integer.")

    years = read_int("Enter simulation duration in years: ", min_value=1, max_value=150)
    output_frequency = read_int("Enter output frequency (1-12 months): ", min_value=1, max_value=12)
    
    bob = Person("Bob", 80000, {
        "rent": 30000,
        "food": 4000,
        "transport": 1500,
        "cat_food": 2000,
        "cat_care": 1500
    })
    
    alice = Person("Alice", 200000, {
        "mortgage": 100000,
        "food": 4000,
        "transport": 1500
    })
    
    simulation = Simulation(years=years, output_frequency=output_frequency, people=[bob, alice])
    
    results = simulation.run()
    simulation.print_results([bob, alice])

    export_payload = {
        "params": {"years": years, "output_frequency": output_frequency},
        "months": results,
        "final": [{"name": p.name, "savings": p.savings} for p in [bob, alice]],
    }
    out_path = Path(__file__).parent / "results.json"
    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(export_payload, file, indent=2)

if __name__ == "__main__":
    main()
