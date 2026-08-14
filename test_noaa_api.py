from data_sources import weather

if __name__ == '__main__':

    print("Starting tests.")

    results = weather.get_metars(['KAWO', 'KOSH', 'KSEA'])

    print("Results:")
    for airport, metar in results.items():
        print(f"{airport}: {metar}")

    print("Tests finished")
