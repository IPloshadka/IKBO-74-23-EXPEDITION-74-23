#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expedition Roster CLI — учебная программа для тестирования методом «чёрного ящика».

Флаг BUG_MODE включает преднамеренные ошибки (по заданию).
Поменяй BUG_MODE на False, чтобы получить «правильное» поведение.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List

# ===================== НАСТРОЙКИ =====================

BUG_MODE = True  # <<< ВКЛ/ВЫКЛ преднамеренные баги
DATA_FILE = "members.json"
ROLES = ("штурман", "водитель", "грузчик", "механик")

# ===================== ВСПОМОГАТЕЛЬНОЕ =====================


def normalize_name(value: str) -> str:
    return value.strip()


def normalize_name_key(value: str) -> str:
    return value.strip().lower()


def normalize_role(value: str) -> str:
    return value.strip().lower()


# ===================== ХРАНИЛИЩЕ =====================


class Store:
    def __init__(self, path: str = DATA_FILE) -> None:
        self.path = path
        self.members: List[Dict[str, str]] = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.members = data if isinstance(data, list) else []
            except Exception:
                print("ERR: ошибка чтения файла данных")
                self.members = []
        else:
            self.members = []

    def save(self) -> None:
        # BUG 7: не создаём файл, если список пуст (приводит к проблемам при следующем запуске)
        if BUG_MODE and len(self.members) == 0:
            return
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.members, f, ensure_ascii=False, indent=2)

    # -------- Операции --------

    def add(self, name: str, role: str) -> tuple[str, str]:
        name = normalize_name(name)
        role_in = role.strip()

        # Валидация роли
        if (role_in.lower() if BUG_MODE else normalize_role(role_in)) not in ROLES:
            # BUG 8: неправильный текст ошибки при неверной роли
            if BUG_MODE:
                return ("ERR", "unknown command")
            return ("ERR", "роль должна быть одной из: " + ", ".join(ROLES))

        # Валидация имени (длина/символы)
        if not BUG_MODE:  # нормальный режим
            if not (2 <= len(name) <= 40):
                return ("ERR", "имя должно быть 2–40 символов (буквы, пробел, дефис)")
            pattern = r"^[A-Za-zА-Яа-яЁё -]{2,40}$"
        else:  # BUG 1: пропускаем короткие/пустые имена
            pattern = r"^[A-Za-zА-Яа-яЁё -]{0,40}$"

        if re.fullmatch(pattern, name) is None:
            return ("ERR", "имя должно быть 2–40 символов (буквы, пробел, дефис)")

        # Уникальность имени
        if BUG_MODE:  # BUG 2: проверка дубликатов чувствительна к регистру
            exists = any(m["name"] == name for m in self.members)
        else:
            key = normalize_name_key(name)
            exists = any(normalize_name_key(m["name"]) == key for m in self.members)
        if exists:
            return ("ERR", "такое имя уже существует")

        # Добавление
        stored_role = role_in if BUG_MODE else normalize_role(role_in)
        self.members.append({"name": name, "role": stored_role})
        self.save()
        shown_role = stored_role if BUG_MODE else normalize_role(stored_role)
        return ("OK", f'добавлен "{name}" ({shown_role})')

    def list_all(self) -> List[Dict[str, str]]:
        if BUG_MODE:
            # Для усиления эффектов персистентности перечитываем с диска перед выводом
            self.load()
            reverse = True  # BUG 3: сортировка по убыванию вместо возрастания
            return sorted(self.members, key=lambda x: x["name"], reverse=reverse)
        return sorted(self.members, key=lambda x: x["name"])

    def list_by_role(self, role: str) -> List[Dict[str, str]]:
        r = role.strip()
        if not BUG_MODE:
            r = normalize_role(r)
            items = [m for m in self.members if normalize_role(m["role"]) == r]
        else:
            # BUG 4: фильтр роли чувствителен к регистру
            items = [m for m in self.members if m["role"] == r]
        reverse = BUG_MODE  # та же «перепутанная» сортировка
        return sorted(items, key=lambda x: x["name"], reverse=reverse)

    def remove(self, name: str) -> tuple[str, str]:
        name = normalize_name(name)
        idx = None
        if BUG_MODE:  # чувствительность к регистру при поиске
            for i, m in enumerate(self.members):
                if m["name"] == name:
                    idx = i
                    break
        else:
            key = normalize_name_key(name)
            for i, m in enumerate(self.members):
                if normalize_name_key(m["name"]) == key:
                    idx = i
                    break

        if idx is None:
            return ("ERR", f'запись с именем "{name}" не найдена')

        del self.members[idx]

        # BUG 6 + 7: если после удаления список пуст — не сохраняем на диск
        # (list перечитывает старый файл и возвращает «устаревший» список)
        if not (BUG_MODE and len(self.members) == 0):
            self.save()

        return ("OK", f'удалён "{name}"')

    def count(self) -> int:
        # BUG 5: занижаем результат на 1 (не ниже 0)
        return max(0, len(self.members) - 1) if BUG_MODE else len(self.members)


# ===================== ПРИНТЕРЫ =====================


def print_list(items: List[Dict[str, str]]) -> None:
    if not items:
        print("нет записей")
        return
    for i, m in enumerate(items, 1):
        print(f'{i}) {m["name"]} — {m["role"]}')


# ===================== REPL =====================


def repl() -> None:
    store = Store()
    print('Учёт экспедиции (CLI). Введите "help" для справки, "exit" для выхода.')
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("exit", "quit"):
            break

        if cmd in ("help", "--help", "-h"):
            print("Доступные команды:")
            print("  add <Имя> <Роль>")
            print("  list")
            print("  list --role <Роль>")
            print("  count")
            print("  remove <Имя>")
            print("  help | exit")
            continue

        if cmd == "add":
            if len(parts) < 3:
                # BUG 15 (сопутствующий): нечёткое сообщение об ошибке формата
                print("ERR: unknown command" if BUG_MODE else "ERR: используйте: add <Имя> <Роль>")
                continue
            name = parts[1]
            role = " ".join(parts[2:])
            status, msg = store.add(name, role)
            print(f"{status}: {msg}")
            continue

        if cmd == "list":
            if len(parts) == 1:
                items = store.list_all()
                print_list(items)
                continue
            if len(parts) >= 3 and parts[1] == "--role":
                role = " ".join(parts[2:])
                items = store.list_by_role(role)
                print_list(items)
                continue
            print("ERR: unknown command")
            continue

        if cmd == "count":
            print(f"Всего участников: {store.count()}")
            continue

        if cmd == "remove":
            if len(parts) < 2:
                print("ERR: используйте: remove <Имя>")
                continue
            name = " ".join(parts[1:])
            status, msg = store.remove(name)
            print(f"{status}: {msg}")
            continue

        print("ERR: unknown command")


if __name__ == "__main__":
    repl()
