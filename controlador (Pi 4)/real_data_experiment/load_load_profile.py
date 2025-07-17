import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def analizar_perfil_de_carga(file_path):
    """
    Lee un archivo CSV con perfiles de carga, permite al usuario seleccionar un país,
    mes y tipo de día, y luego grafica la carga y la carga normalizada para el día
    seleccionado.

    Args:
        file_path (str): La ruta al archivo CSV.
    """
    try:
        # 1. Leer el archivo con pandas
        df = pd.read_csv(file_path)

        # 2. Mostrar información al usuario
        # Países disponibles
        available_countries = sorted(df['NUTS0_code'].unique())
        print("Países disponibles:", ", ".join(available_countries))

        # 3. Selección del usuario
        country = ''
        while country not in available_countries:
            country = input(f"Seleccione un país de la lista: ").upper()
            if country not in available_countries:
                print(f"País no válido. Por favor, elija uno de: {', '.join(available_countries)}")

        # Filtrar el DataFrame por el país seleccionado
        df_country = df[df['NUTS0_code'] == country]

        # Mostrar el rango de "fechas" (perfiles) para el país seleccionado
        available_months = sorted(df_country['month'].unique())
        available_daytypes = sorted(df_country['daytype'].unique())

        print(f"\n--- Perfiles disponibles para {country} ---")
        print(f"El rango de fechas detectado corresponde a los siguientes perfiles:")
        print(f"Meses disponibles: {available_months}")
        print(f"Tipos de día (daytype) disponibles: {available_daytypes}")
        print("------------------------------------")
        
        # Pedir al usuario que seleccione un perfil (día)
        selected_month = 0
        while selected_month not in available_months:
            try:
                selected_month = int(input(f"Seleccione un mes ({min(available_months)}-{max(available_months)}): "))
                if selected_month not in available_months:
                    print("Mes no válido. Por favor, intente de nuevo.")
            except ValueError:
                print("Por favor, ingrese un número válido.")

        selected_daytype = -1
        while selected_daytype not in available_daytypes:
            try:
                selected_daytype = int(input(f"Seleccione un tipo de día {available_daytypes}: "))
                if selected_daytype not in available_daytypes:
                    print("Tipo de día no válido. Por favor, intente de nuevo.")
            except ValueError:
                print("Por favor, ingrese un número válido.")

        # 4. Filtrar datos para el perfil seleccionado
        day_data = df_country[
            (df_country['month'] == selected_month) &
            (df_country['daytype'] == selected_daytype)
        ].copy() # Usar .copy() para evitar SettingWithCopyWarning

        if day_data.empty:
            print("No se encontraron datos para la selección. Terminando programa.")
            return
            
        # Asegurarse de que los datos estén ordenados por hora para el gráfico
        day_data = day_data.sort_values('hour')

        # 5. Normalizar la columna "load"
        max_load = day_data['load'].max()
        if max_load > 0:
            day_data['load_normalized'] = (day_data['load'] / max_load) * 100
        else:
            day_data['load_normalized'] = 0 # Evitar división por cero si la carga máxima es 0

        # 6. Graficar
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(f'Perfil de Carga para {country} | Mes: {selected_month}, Tipo de Día: {selected_daytype}', fontsize=16)

        # Gráfico 1: Carga vs Tiempo
        ax1.plot(day_data['hour'], day_data['load'], marker='o', linestyle='-')
        ax1.set_title('Perfil de Carga Absoluta')
        ax1.set_ylabel('Carga (load)')
        ax1.grid(True)
        
        # Gráfico 2: Carga Normalizada vs Tiempo
        ax2.plot(day_data['hour'], day_data['load_normalized'], marker='o', linestyle='-', color='g')
        ax2.set_title('Perfil de Carga Normalizada')
        ax2.set_xlabel('Hora del día')
        ax2.set_ylabel('Carga Normalizada')
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())
        ax2.set_ylim(0, 110) # Dejar un poco de espacio sobre el 100%
        ax2.grid(True)
        
        # Mejorar las etiquetas del eje x para que se muestren todas las horas
        plt.xticks(range(1, 25))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Ajustar para el suptitle
        plt.show()

    except FileNotFoundError:
        print(f"Error: El archivo no se encontró en la ruta '{file_path}'")
    except KeyError as e:
        print(f"Error: La columna esperada '{e}' no se encontró en el archivo CSV.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# --- Ejecución del script ---
# Reemplaza esta ruta con la ubicación de tu archivo CSV.
# Se utiliza una cadena "raw" (r'...') para evitar problemas con las barras invertidas en Windows.
#file_path = r'c:\Users\Pablo Castillo\OneDrive - fraunhofer.cl\Documentos\GitHub\Thermial\controlador (Pi 4)\real_data_experiment\load_profiles\hotmaps_task_2.7_load_profile_industry_chemicals_and_petrochemicals_generic.csv'
file_path = r'C:\Users\Pablo Castillo\OneDrive - fraunhofer.cl\Documentos\GitHub\Thermial\controlador (Pi 4)\real_data_experiment\load_profiles\hotmaps_task_2.7_load_profile_industry_food_and_tobacco_generic.csv'
analizar_perfil_de_carga(file_path)
