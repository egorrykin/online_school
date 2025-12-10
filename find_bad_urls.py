import os
import re

def find_syntax_errors():
    """Найти синтаксические ошибки в шаблонах"""
    templates_dir = 'templates'
    errors = []

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                # Проверяем на некорректные теги
                for i, line in enumerate(lines, 1):
                    # Ищем странные конструкции с {% внутри переменных
                    if 'course.{%' in line or '{% endwith %}{% endwith %}' in line or '{% with' in line and '{% endwith %}' not in line:
                        errors.append(f'Файл: {filepath}, Строка {i}: {line.strip()}')

    return errors

if __name__ == '__main__':
    print('Поиск синтаксических ошибок в шаблонах...')
    errors = find_syntax_errors()

    if errors:
        print('\n=== Найдены ошибки: ===')
        for error in errors:
            print(error)
    else:
        print('\n✅ Синтаксических ошибок не найдено!')