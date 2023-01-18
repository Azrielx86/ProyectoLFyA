import re
import curses
from os import get_terminal_size
from time import sleep
from typing import Literal, Dict
from cursesmenu import *
from cursesmenu.items import *
from argparse import ArgumentParser
from art import text2art

ARROW_UP = [
    "     .     ",
    "   .:;:.   ",
    " .:;;;;;:. ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
]

ARROW_DOWN = [
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    "   ;;;;;   ",
    " ..;;;;;.. ",
    "  ':::::'  ",
    "    ':`    ",
]


class State:
    """Representa una transición"""

    def __init__(self, name: str, is_start=False, is_final=False) -> None:
        """
        @param name El nombre del estado. @param is_start Si este estado es o no
        el estado de inicio. @param is_final Si el estado es un estado final
        """
        self.__name: str = name
        self.__is_start: bool = is_start
        self.__is_final: bool = is_final
        self.__transitions: Dict[Literal["0", "1"], "State"] = {}

    @property
    def name(self) -> str:
        return self.__name

    @property
    def is_start(self) -> bool:
        return self.__is_start

    @property
    def is_final(self) -> bool:
        return self.__is_final

    def add_transition(self, state_to: "State", character: Literal["0", "1"]):
        """
        Añade una transición al estado.

        @param state_to El estado al que se realiza la transición. @param
        character Literales["0", "1"] pertenecientes al alfabeto
        """
        if state_to not in self.__transitions:
            self.__transitions[character] = state_to
        else:
            raise Exception(f"El estado ya tiene una transición {character}")

    def __getitem__(self, key: Literal["0", "1"] | str) -> "State":
        if key in self.__transitions.keys():
            return self.__transitions[key]
        else:
            raise Exception("El estado no existe")

    def __str__(self) -> str:
        return f"{self.__name}"


class AFD:
    """Representa un Autómata Finito Determinístico con sus transiciones"""

    def __init__(self) -> None:
        self.__states: Dict[str, State] = {}
        self.__start: State | None = None

    def __setitem__(self, key: str, item: State) -> None:
        if isinstance(item, State):
            if key not in self.__states.keys():
                self.__states[key] = item
                if item.is_start:
                    if self.__start is None:
                        self.__start = item
                    else:
                        raise Exception("No se puede tener más de un estado inicial")

    def __getitem__(self, key: str) -> State:
        if key in self.__states.keys():
            return self.__states[key]
        else:
            raise Exception("El estado no existe")

    def execute_string(self, string: str) -> int:
        """Comprueba si una cadena es válida para el autómata y retorna el
        número de pasos que dió"""
        state = self.__start[string[0]]
        steps = 1
        for character in string[1:-1]:
            state = state[character]
            steps += 1

        state = state[string[-1]]

        if not state.is_final:
            raise Exception("La cadena no es válida para el autómata")

        return steps


class Elevator:
    """Representa un elevador"""

    def __init__(self, floors: int) -> None:
        """
        Inicializa la clase Ascensor con el número de pisos y crea un autómata
        que tiene tres estados: DET (Detenido), SUB (Subiendo) y BAJ (Bajando)

        @param floors El número de pisos en el edificio.
        """
        self.__automata = AFD()
        self.__floors = floors
        self.__current_floor = 0

        self.__automata["DET"] = State("DET", is_start=True, is_final=True)
        self.__automata["SUB"] = State("SUB")
        self.__automata["BAJ"] = State("BAJ")

        self.__automata["DET"].add_transition(self.__automata["SUB"], "1")
        self.__automata["DET"].add_transition(self.__automata["BAJ"], "0")
        self.__automata["SUB"].add_transition(self.__automata["SUB"], "0")
        self.__automata["SUB"].add_transition(self.__automata["DET"], "1")
        self.__automata["BAJ"].add_transition(self.__automata["BAJ"], "0")
        self.__automata["BAJ"].add_transition(self.__automata["DET"], "1")

    @property
    def floors(self) -> int:
        return self.__floors

    @property
    def current_floor(self) -> int:
        return self.__current_floor

    def floor_up(self, to: int) -> None:
        """Sube un piso"""
        if to > self.__floors:
            raise Exception(f"Máximo {self.__floors} pisos")

        steps = "1" + "".join(["0" for i in range(to - self.__current_floor - 1)]) + "1"
        try:
            self.__current_floor += self.__automata.execute_string(steps)
        except Exception as e:
            print(f"Error al subir: {e}")

    def floor_down(self, to: int) -> None:
        """Baja un piso"""
        if to < 0:
            raise Exception("No es posible bajar menos pisos")
        if self.__current_floor - to < 0:
            raise Exception("No es posible bajar menos pisos")

        steps = "0" + "".join(["0" for i in range(self.__current_floor - to - 1)]) + "1"
        try:
            self.__current_floor -= self.__automata.execute_string(steps)
        except Exception as e:
            print(f"Error al bajar: {e}")


def curses_animation(menu: CursesMenu, from_f: int, to_f: int):
    menu.pause()
    stdscr = curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    stdscr.border(0)
    stdscr.refresh()

    arrow_pad = curses.newpad(11, 9)
    floor_pad = curses.newpad(20, 20)
    stdscr.refresh()

    arr_dir = ARROW_DOWN if from_f > to_f else ARROW_UP

    count = from_f - to_f if from_f > to_f else to_f - from_f

    for steps in range(count + 1):
        floor = re.split("\n", text2art(str(steps + from_f if from_f < to_f else from_f - steps)))
        floor_pad.clear()
        floor_pad.refresh(0, 0, 5, 16, 15, 25)

        for fi, f in enumerate(floor):
            floor_pad.addstr(fi, 0, f)
        floor_pad.refresh(0, 0, 5, 16, 15, 25)

        for i in range(len(arr_dir)):
            arrow_pad.clear()
            arrow_pad.refresh(i if from_f < to_f else 5 - i, 0, 5, 5, 16, 15)

            for j, w in enumerate(arr_dir):
                arrow_pad.addstr(j, 0, w)

            arrow_pad.refresh(i if from_f < to_f else 5 - i, 0, 5, 5, 16, 15)
            sleep(0.05)

    stdscr.clear()
    curses.curs_set(0)
    stdscr.refresh()
    menu.resume()


def goto_floor(elevator: Elevator, floor: int, menu: CursesMenu):
    from_f = elevator.current_floor
    to_f = floor

    if floor > elevator.current_floor:
        elevator.floor_up(floor)
    elif floor < elevator.current_floor:
        elevator.floor_down(floor)
    else:
        pass

    menu.title = f"Elevador - Piso actual: {elevator.current_floor if elevator.current_floor != 0 else 'Planta baja'}"

    curses_animation(menu, from_f, to_f)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--pisos", type=int, default=5)

    args = parser.parse_args()

    elevator = Elevator(args.pisos + 1)

    print(" Proyecto Lenguajes Formales y Autómatas ".center(get_terminal_size().columns, "="))

    menu = CursesMenu("Elevador - Piso actual: Planta baja")
    for i in range(elevator.floors, 0, -1):
        item = FunctionItem(
            text=f"Piso {i}", function=goto_floor, args=[elevator, i, menu], menu=menu, override_index=i
        )
        menu.items.append(item)
    menu.items.append(
        FunctionItem(text="Planta baja", function=goto_floor, args=[elevator, 0, menu], menu=menu, override_index=0)
    )

    menu.show()
