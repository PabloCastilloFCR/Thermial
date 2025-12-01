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
            date_str = df['date'].iloc[0]
            experiment_date = pd.to_datetime(date_str, dayfirst=True).strftime('%Y-%m-%d')
        except (IndexError, KeyError, ValueError):
            # Fallback if 'Fecha' column is missing, empty, or has an unexpected format.
            experiment_date = "Unknown date"

        # Combine 'Fecha' and 'Hora' into a single datetime column.
        df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], dayfirst=True)

        # Set the new 'Timestamp' column as the index for easier time-series plotting.
        df.set_index('timestamp', inplace=True)

        # Clean up column names for easier access (remove special characters and spaces).
        # This is a good practice for writing clean code.
        df.columns = [
            'date', 'time',
            'power_pump1_pct', 'flow_pump1_L_min',
            'power_heater1_pct', 'power_heater1_W',
            'temp_heater1_in_C', 'temp_heater1_out_C',
            'power_heater2_pct', 'power_heater2_W', 'temp_heater2_out_C',
            'valve1_state', 'flow_valve1_out_L_min', 'valve2_state',
            'flow_valve2_out_L_min', 'level_tank_cm', 
            'temp_tank_bottom_C', 'temp_tank_top_C',
            'power_pump2_pct', 'flow_pump2_L_min',
            'power_radiator1_pct', 'power_radiator1_W',
            'temp_radiator1_in_C', 'temp_radiator1_out_C'
        ]

        print("Data loaded and prepared successfully. Columns available:")
        print(df.columns)

        # --- 3. Plotting ---

        # Create a figure with 2x2 subplots for a comprehensive overview.
        fig, axs = plt.subplots(2, 2, figsize=(16, 9), sharex=True) #oder (12, 7)
        fig.suptitle(f'Análisis de Datos del Experimento - {experiment_date}', fontsize=16)

        # Plot 1: Inlet and Outlet Temperatures of the heater
        axs[0, 0].plot(df.index, df['temp_heater1_in_C'], label='Inlet temperature heater 1 (°C)', color='blue')
        axs[0, 0].plot(df.index, df['temp_heater1_out_C'], label='Outlet temperature heater 1 (°C)', color='orange')
        axs[0, 0].plot(df.index, df['temp_radiator1_in_C'], label='Inlet temperature radiator 1 (°C)', color='green')
        axs[0, 0].plot(df.index, df['temp_radiator1_out_C'], label='Outlet temperature radiator 1 (°C)', color='turquoise')
        axs[0, 0].set_ylabel('Temperature (°C)')
        axs[0, 0].set_title('Temperatures of the heater and radiator')
        axs[0, 0].legend()
        axs[0, 0].grid(True, linestyle='--', alpha=0.6)

        # Plot 2: Tank Temperatures
        axs[0, 1].plot(df.index, df['temp_tank_bottom_C'], label='Bottom tank temperature (°C)', color='#FFB347')
        axs[0, 1].plot(df.index, df['temp_tank_top_C'], label='Top tank temperature (°C)', color='brown')
        axs[0, 1].plot(df.index, df['temp_heater2_out_C'], label='Outlet temperature heater 2 (°C)', marker='^', color='green')
        axs[0, 1].set_ylabel('Temperature (°C)')
        axs[0, 1].set_title('Temperatures of the tank')
        axs[0, 1].legend()
        axs[0, 1].grid(True, linestyle='--', alpha=0.6)

        # Plot 3: Inlet and Outlet Temperatures of the radiator
        #axs[0, 0].plot(df.index, df['temp_radiator1_in_C'], label='Inlet temperature radiator 1 (°C)', color='green')
        #axs[0, 0].plot(df.index, df['temp_radiator1_out_C'], label='Outlet temperature radiator 1 (°C)', color='turquoise')
        #axs[0, 0].set_ylabel('Temperature (°C)')
        #axs[0, 0].set_title('Temperatures of the radiator')
        #axs[0, 0].legend()
        #axs[0, 0].grid(True, linestyle='--', alpha=0.6)

        # Plot 3: Power Percentages
        axs[1, 0].plot(df.index, df['power_pump1_pct'] + 0.2, label='Power pump 1 (%)', linestyle='--', marker='o', markevery=50, markersize=6, color='tab:red', linewidth=0.8)
        axs[1, 0].plot(df.index, df['power_pump2_pct'], label='Power pump 2 (%)', linestyle=':', color='tab:purple', linewidth=2.5)
        axs[1, 0].plot(df.index, df['power_heater1_pct'], label='Power heater 1 (%)', linestyle='--', marker='s', markevery=(20, 50), markersize=6, color='tab:orange', linewidth=2.5)
        axs[1, 0].plot(df.index, df['power_heater2_pct'], label='Power heater 2 (%)', linestyle='--', marker='^', markevery=(40, 50), markersize=6, color='green', linewidth=2.5)
        axs[1, 0].set_ylabel('Power (%)')
        axs[1, 0].set_title('Power of the components')
        axs[1, 0].legend(handlelength=3)
        axs[1, 0].grid(True, linestyle='--', alpha=0.6)
        axs[1, 0].set_ylim(-4, 104)
        axs[1, 0].set_yticks([0, 20, 40, 60, 80, 100])
        #axs[1, 0].set_ylim(0, 102)

        # Plot 4: Flow Rates
        axs[1, 1].plot(df.index, df['flow_pump1_L_min'], label='Flow pump 1 (L/min)', color='tab:red', linewidth=0.8) #, 
        axs[1, 1].plot(df.index, df['flow_valve1_out_L_min'], label='Flow valve 1 (L/min)', color='black', linewidth=0.8) #linestyle='--',
        axs[1, 1].plot(df.index, df['flow_pump2_L_min'], label='Flow pump 2 (L/min)', linestyle=':', color='tab:purple')

        axs[1, 1].set_ylabel('Flow (L/min)')
        axs[1, 1].set_title('Flows of the solar and process loop')
        axs[1, 1].legend()
        axs[1, 1].grid(True, linestyle='--', alpha=0.6)


        # Improve formatting for all subplots
        for ax in axs.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
            # Volle Zeitachse von Start bis Ende
            start_time = df.index.min()
            end_time = df.index.max()
            ax.set_xlim(start_time, end_time)

            tick_start = start_time.floor('5T')
            tick_end = end_time.ceil('5T')
            ax.set_xticks(pd.date_range(start=tick_start, end=tick_end, freq='20T'))


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
    file_path = "/home/thermial/Desktop/test_data/solarloop_test_20251106_150042.csv"
    plot_solar_loop_data(file_path)

