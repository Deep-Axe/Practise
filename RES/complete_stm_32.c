/* USER CODE BEGIN Header */
/* USER CODE END Header */

#include "main.h"

/* USER CODE BEGIN Includes */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
/* USER CODE END Includes */

DAC_HandleTypeDef hdac;
TIM_HandleTypeDef htim2;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
char rx_buf[32];
uint8_t rx_index = 0;
uint8_t rx_char;
#define MOTOR_MIN_V 0.55f

// PD Controller state
float current_dac_voltage = 0.0f;
float prev_desired = 0.0f;
uint32_t last_update_tick = 0;

#define KP_DOWN        1.0f
#define KP_UP          0.6f
#define KD             0.05f
#define DROP_THRESHOLD 1.5f
#define DECEL_WEIGHT   0.8f
#define UPDATE_PERIOD  50
#define MIN_VEL        3.0f
#define MAX_VEL        5.0f
/* USER CODE END PV */

void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DAC_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_TIM2_Init(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_DAC_Init();
  MX_USART2_UART_Init();
  MX_TIM2_Init();

  /* USER CODE BEGIN 2 */
  // 1. Start DAC
  HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
  HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 0);

  // 2. Start Steering PWM (Center servo at 1500us)
  HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
  __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, 1500);

  // 3. Ensure Brake is OFF
  HAL_GPIO_WritePin(BRAKE_GPIO_Port, BRAKE_Pin, GPIO_PIN_RESET);

  // 4. Start UART Interrupt
  char *welcome = "STM32 Unified Controller Ready...\r\n";
  HAL_UART_Transmit(&huart2, (uint8_t*)welcome, strlen(welcome), 100);
  HAL_UART_Receive_IT(&huart2, &rx_char, 1);
  /* USER CODE END 2 */

  while (1)
  {
  }
}

/* USER CODE BEGIN 4 */
static float vel_to_voltage(float vel)
{
    #define MOTOR_MIN_V_INTERNAL  0.5f
    if (vel < MIN_VEL) vel = MIN_VEL;
    if (vel > MAX_VEL) vel = MAX_VEL;
    float t = (vel - MIN_VEL) / (MAX_VEL - MIN_VEL);
    return MOTOR_MIN_V_INTERNAL + t * (3.3f - MOTOR_MIN_V_INTERNAL);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2)
    {
        if (rx_char == '\r' || rx_char == '\n')
        {
            rx_buf[rx_index] = '\0';

            if (rx_index > 0)
            {
                // ==========================================
                // 1. PARSE STEERING (e.g., "S:135")
                // ==========================================
                if (strncmp(rx_buf, "S:", 2) == 0)
                {
                    int angle = atoi(rx_buf + 2);
                    if (angle < 0) angle = 0;
                    if (angle > 270) angle = 270;
                    
                    // Map 0-270 degrees to 500-2500 microsecond pulse width
                    uint32_t pulse_length = 500 + ((uint32_t)angle * 2000 / 270);
                    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, pulse_length);
                }
                
                // ==========================================
                // 2. PARSE BRAKE (e.g., "B:1" or "B:0")
                // ==========================================
                else if (strncmp(rx_buf, "B:", 2) == 0)
                {
                    int brake_val = atoi(rx_buf + 2);
                    HAL_GPIO_WritePin(BRAKE_GPIO_Port, BRAKE_Pin, brake_val ? GPIO_PIN_SET : GPIO_PIN_RESET);
                }
                
                // ==========================================
                // 3. PARSE VELOCITY (e.g., "V:4.5")
                // ==========================================
                else if (strncmp(rx_buf, "V:", 2) == 0)
                {
                    uint32_t now = HAL_GetTick();
                    if ((now - last_update_tick) >= UPDATE_PERIOD)
                    {
                        last_update_tick = now;

                        float desired_vel = atof(rx_buf + 2);
                        if (desired_vel < 0.0f) desired_vel = 0.0f;
                        if (desired_vel > MAX_VEL) desired_vel = MAX_VEL;

                        float desired_voltage = vel_to_voltage(desired_vel);

                        float drop = prev_desired - desired_voltage;
                        if (drop > DROP_THRESHOLD)
                        {
                            current_dac_voltage = 0.0f;
                            prev_desired = desired_voltage;
                            HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 0);
                        }
                        else 
                        {
                            if (desired_voltage < current_dac_voltage)
                            {
                                desired_voltage = desired_voltage * DECEL_WEIGHT;
                            }

                            float error = desired_voltage - current_dac_voltage;
                            float derivative = desired_voltage - prev_desired;
                            float kp = (desired_voltage < current_dac_voltage) ? KP_DOWN : KP_UP;

                            float output = current_dac_voltage + kp * error + KD * derivative;

                            if (output < 0.0f) output = 0.0f;
                            if (output > 3.3f) output = 3.3f;
                            if (output > 0.0f && output < MOTOR_MIN_V) output = MOTOR_MIN_V;

                            current_dac_voltage = output;
                            prev_desired = desired_voltage;

                            uint32_t dac_value = (uint32_t)((current_dac_voltage / 3.3f) * 4095.0f);
                            HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_value);
                        }
                    }
                }
            }
            rx_index = 0;
        }
        else if (rx_index < sizeof(rx_buf) - 1)
        {
            rx_buf[rx_index++] = rx_char;
        }
        
        HAL_UART_Receive_IT(&huart2, &rx_char, 1);
    }
}
/* USER CODE END 4 */

void Error_Handler(void)
{
  __disable_irq();
  while (1) {}
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line) {}
#endif

// --- AUTO-GENERATED INITIALIZATION FUNCTIONS BELOW THIS LINE ---
// (CubeMX will output MX_GPIO_Init, MX_DAC_Init, MX_USART2_UART_Init, MX_TIM2_Init here)
// (DO NOT overwrite your auto-generated config functions at the bottom of the file)
