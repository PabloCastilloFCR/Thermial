import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_solar_loop_data(csv_filepath):
    """
    Loads, processes, and plots experimental data from a semicolon-separated CSV file.

    Args:
        csv_filepath (str): The full path to the CSV file.
    """
    try:
        # --- 1. Load Data ---
        # Read the CSV file, specifying the semicolon separator and comma decimal point.
        df = pd.read_csv(
            csv_filepath,
            sep=';',
            decimal=','
        )

        # --- 2. Data Cleaning and Preparation ---

        # Extract experiment date from the 'Fecha' column for a more robust title.
        try:
            # Get the date from the first row, assuming it's constant for the experiment.
            # The dayfirst=True argument correctly interprets DD/MM/YYYY format.
            date_str = df['Fecha'].iloc[0]
            experiment_date = pd.to_datetime(date_str, dayfirst=True).strftime('%Y-%m-%d')
        except (IndexError, KeyError, ValueError):
            # Fallback if 'Fecha' column is missing, empty, or has an unexpected format.
            experiment_date = "Fecha Desconocida"

        # Combine 'Fecha' and 'Hora' into a single datetime column.
        df['Timestamp'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora'], dayfirst=True)

        # Set the new 'Timestamp' column as the index for easier time-series plotting.
        df.set_index('Timestamp', inplace=True)

        # Clean up column names for easier access (remove special characters and spaces).
        # This is a good practice for writing clean code.
        df.columns = [
            'Fecha', 'Hora',
            'Bomba1_Potencia_pct', 'Bomba1_Flujo_L_min',
            'Calentador_Potencia_pct', 'Calentador_Potencia_W',
            'Temp_1_Entrada_C', 'Temp_2_Salida_C',
            'Valvula1_Estado', 'Valvula2_Estado',
            'Valvula1_Flujo_L_min', 'Valvula2_Flujo_L_min',
            'Nivel_Estanque_cm', 'Estanque_Temp3_C', 'Estanque_Temp4_C',
            'Bomba2_Potencia_pct', 'Bomba2_Flujo_L_min',
            'Dissipador_Potencia_pct', 'Dissipador_Temp5_C', 'Dissipador_Temp6_C'
        ]

        print("Data loaded and prepared successfully. Columns available:")
        print(df.columns)

        # --- 3. Plotting ---

        # Create a figure with 2x2 subplots for a comprehensive overview.
        fig, axs = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
        fig.suptitle(f'Análisis de Datos del Experimento - {experiment_date}', fontsize=16)

        # Plot 1: Inlet and Outlet Temperatures
        axs[0, 0].plot(df.index, df['Temp_1_Entrada_C'], label='Temp. Entrada (°C)', color='red')
        axs[0, 0].plot(df.index, df['Temp_2_Salida_C'], label='Temp. Salida (°C)', color='blue')
        axs[0, 0].set_ylabel('Temperatura (°C)')
        axs[0, 0].set_title('Temperaturas del Calentador')
        axs[0, 0].legend()
        axs[0, 0].grid(True, linestyle='--', alpha=0.6)

        # Plot 2: Tank Temperatures
        axs[0, 1].plot(df.index, df['Estanque_Temp3_C'], label='Temp. Estanque 3 (°C)', color='purple')
        axs[0, 1].plot(df.index, df['Estanque_Temp4_C'], label='Temp. Estanque 4 (°C)', color='orange')
        axs[0, 1].set_ylabel('Temperatura (°C)')
        axs[0, 1].set_title('Temperaturas del Estanque')
        axs[0, 1].legend()
        axs[0, 1].grid(True, linestyle='--', alpha=0.6)

        # Plot 3: Power Percentages
        axs[1, 0].plot(df.index, df['Bomba1_Potencia_pct'], label='Potencia Bomba (%)', linestyle='--')
        axs[1, 0].plot(df.index, df['Calentador_Potencia_pct'], label='Potencia Calentador (%)', linestyle=':')
        axs[1, 0].set_ylabel('Potencia (%)')
        axs[1, 0].set_title('Potencia de Componentes')
        axs[1, 0].legend()
        axs[1, 0].grid(True, linestyle='--', alpha=0.6)
        axs[1, 0].set_ylim(0, 100)

        # Plot 4: Flow Rates
        axs[1, 1].plot(df.index, df['Bomba1_Flujo_L_min'], label='Flujo Bomba (L/min)')
        axs[1, 1].plot(df.index, df['Valvula1_Flujo_L_min'], label='Flujo Válvula 1 (L/min)', linestyle='--')
        axs[1, 1].set_ylabel('Flujo (L/min)')
        axs[1, 1].set_title('Flujos del Sistema')
        axs[1, 1].legend()
        axs[1, 1].grid(True, linestyle='--', alpha=0.6)

        # Improve formatting for all subplots
        for ax in axs.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
        save_path = r"C:\Users\Ricarda-Laura Sack\Desktop\Proyecto Ricarda\Experimentos\Calentador y sensores de temperatura\Plots\plot_experiment1.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Plot saved to: {save_path}")
        plt.show()

    except FileNotFoundError:
        print(f"Error: The file was not found at {csv_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # --- IMPORTANT ---
    # Replace this with the actual path to your CSV file.
   # file_path = r'c:\Users\Pablo Castillo\OneDrive - fraunhofer.cl\Documentos\01. RESEARCH\01. THERMIAL\06. Resultados\solarloop_test_20250625.csv'
    file_path = "/home/thermial/Desktop/test_data/both_loops_2025-10-13_12-29-18.csv"
    plot_solar_loop_data(file_path)

