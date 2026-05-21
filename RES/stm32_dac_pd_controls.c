/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

#include "main.h"

/* USER CODE BEGIN Includes */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
/* USER CODE END Includes */

DAC_HandleTypeDef hdac;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
char rx_buf[16];
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

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_DAC_Init();
  MX_USART2_UART_Init();

  /* USER CODE BEGIN 2 */
  HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
  HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 0);

  char *welcome = "STM32 DAC Ready - Waiting for velocity data...\r\n";
  HAL_UART_Transmit(&huart2, (uint8_t*)welcome, strlen(welcome), 100);

  HAL_UART_Receive_IT(&huart2, &rx_char, 1);
  /* USER CODE END 2 */

  while (1)
  {
  }
}

void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 180;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  if (HAL_PWREx_EnableOverDrive() != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                               | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_DAC_Init(void)
{
  DAC_ChannelConfTypeDef sConfig = {0};

  hdac.Instance = DAC;
  if (HAL_DAC_Init(&hdac) != HAL_OK)
  {
    Error_Handler();
  }

  sConfig.DAC_Trigger = DAC_TRIGGER_NONE;
  sConfig.DAC_OutputBuffer = DAC_OUTPUTBUFFER_ENABLE;
  if (HAL_DAC_ConfigChannel(&hdac, &sConfig, DAC_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_USART2_UART_Init(void)
{
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  HAL_GPIO_WritePin(LD2_GPIO_Port, LD2_Pin, GPIO_PIN_RESET);

  GPIO_InitStruct.Pin = B1_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(B1_GPIO_Port, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LD2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LD2_GPIO_Port, &GPIO_InitStruct);
}

/* USER CODE BEGIN 4 */

static float vel_to_voltage(float vel)
{
	#define MOTOR_MIN_V  0.5f   // voltage at which motor actually starts spinning
    if (vel < MIN_VEL) vel = MIN_VEL;
    if (vel > MAX_VEL) vel = MAX_VEL;
    float t = (vel - MIN_VEL) / (MAX_VEL - MIN_VEL);
    return MOTOR_MIN_V + t * (3.3f - MOTOR_MIN_V);
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
                // --- Rate limit to ~10Hz ---
                uint32_t now = HAL_GetTick();
                if ((now - last_update_tick) < UPDATE_PERIOD)
                {
                    rx_index = 0;
                    HAL_UART_Receive_IT(&huart2, &rx_char, 1);
                    return;
                }
                last_update_tick = now;

                // --- Parse incoming velocity (3.0 to 5.0 m/s) ---
                float desired_vel = atof(rx_buf);
                if (desired_vel < 0.0f) desired_vel = 0.0f;
                if (desired_vel > MAX_VEL) desired_vel = MAX_VEL;

                // Convert to target voltage
                float desired_voltage = vel_to_voltage(desired_vel);

                // --- Rule 1: Large drop → hard brake to 0V ---
                float drop = prev_desired - desired_voltage;
                if (drop > DROP_THRESHOLD)
                {
                    current_dac_voltage = 0.0f;
                    prev_desired = desired_voltage;

                    HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, 0);

                    // Split drop float for print
                    int drop_int = (int)drop;
                    int drop_frac = (int)((drop - drop_int) * 100);

                    char msg[64];
                    int len = sprintf(msg, "BRAKE: drop=%d.%02d -> 0.00V\r\n",
                                     drop_int, drop_frac);
                    HAL_UART_Transmit(&huart2, (uint8_t*)msg, len, 100);

                    rx_index = 0;
                    HAL_UART_Receive_IT(&huart2, &rx_char, 1);
                    return;
                }

                // --- Rule 2: Deceleration bias ---
                // Scale desired voltage down when slowing
                if (desired_voltage < current_dac_voltage)
                {
                    desired_voltage = desired_voltage * DECEL_WEIGHT;
                }

                // --- PD Controller ---
                float error = desired_voltage - current_dac_voltage;
                float derivative = desired_voltage - prev_desired;
                float kp = (desired_voltage < current_dac_voltage) ? KP_DOWN : KP_UP;

                float output = current_dac_voltage + kp * error + KD * derivative;

                // Clamp
                if (output < 0.0f) output = 0.0f;
                if (output > 3.3f) output = 3.3f;

                if (output > 0.0f && output < MOTOR_MIN_V)
                    output = MOTOR_MIN_V;

                current_dac_voltage = output;
                prev_desired = desired_voltage;

                // Convert to 12-bit DAC value
                uint32_t dac_value = (uint32_t)((current_dac_voltage / 3.3f) * 4095.0f);
                HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_value);

                // Debug print (no floats in sprintf)
                int v_int  = (int)current_dac_voltage;
                int v_frac = (int)((current_dac_voltage - v_int) * 100);
                int vel_int  = (int)desired_vel;
                int vel_frac = (int)((desired_vel - vel_int) * 100);

                char msg[128];
                int len = sprintf(msg, "Vel: %d.%02d -> DAC: %lu -> %d.%02dV\r\n",
                                 vel_int, vel_frac, dac_value, v_int, v_frac);
                HAL_UART_Transmit(&huart2, (uint8_t*)msg, len, 100);
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
  while (1)
  {
  }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
}
#endif
