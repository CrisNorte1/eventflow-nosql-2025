from typing import Any, Callable, List, Optional


class SagaError(Exception):
    """Excepcion de dominio para indicar un fallo dentro de la Saga."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class SagaStep:
    """Representa un paso de la Saga con su accion principal y su compensacion."""

    def __init__(
        self,
        name: str,
        action: Callable[[Any], None],
        compensation: Optional[Callable[[Any], None]] = None,
    ):
        self.name = name
        self.action = action
        self.compensation = compensation


class Saga:
    """Motor simple de Saga orquestada."""

    def __init__(self, steps: List[SagaStep]):  # Es la lista de pasos de la saga
        self.steps = steps

    def execute(self, context: Any):  # Ejecuta la saga con el contexto dado (cualquier objeto)
        executed: List[SagaStep] = []  # Pasos ejecutados exitosamente
        try:
            for step in self.steps:
                step.action(context)  # Ejecuta la accion del paso y si es exitosa lo marca como ejecutado
                executed.append(step)
        except SagaError:  # Si da un error de dominio, compensa los pasos ejecutados
            self._compensate(context, executed)
            raise
        except Exception as exc:  # Envolvemos fallos inesperados
            self._compensate(context, executed)
            raise SagaError(str(exc)) from exc

    @staticmethod
    def _compensate(context: Any, executed: List[SagaStep]):  # Toma los pasos ejecutados y llama a sus compensaciones
        for step in reversed(executed):
            if step.compensation:
                try:
                    step.compensation(context)
                except Exception:
                    pass
