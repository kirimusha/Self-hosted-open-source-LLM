<img width="2523" height="1614" alt="self-hosted_open-source_LLM excalidraw" src="https://github.com/user-attachments/assets/7a20018e-fd04-42dc-94bc-7459e0f34f8e" />


# Self-hosted-open-source-LLM
Self-hosted веб-приложение, которое позволяет пользователю ввести описание конечной цели проекта и  получить готовую иерархическую структуру работ (ИСР) в формате документа или таблицы. Система включает в себя базу знаний с ГОСТами и стандартами, а также понятную админку для её пополнения неподготовленным пользователем.

Инструкция по запуску

Шаг 1: Скачать модель
''
bash
chmod +x download_model.sh
./download_model.sh
''

Шаг 2: Подготовить базу знаний
'''
bash
mkdir -p knowledge_base/gosts knowledge_base/examples
'''

# Положите ваши ГОСТы в knowledge_base/gosts/

Шаг 3: Запустить систему
'''
bash
docker-compose up -d
'''

Шаг 4: Проверить работу
'''
bash
'''
# Проверка здоровья
'''
curl http://localhost:8000/health
'''
# Генерация ИСР
'''
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"goal": "Разработать систему автоматизации документооборота", "username": "test"}'
'''
