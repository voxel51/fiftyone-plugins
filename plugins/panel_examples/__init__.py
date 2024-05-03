import fiftyone.operators as foo
import fiftyone.operators.types as types

class IncCountPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="inc_count_panel",
            label="Example: Increment Count"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
        
    def render(self, ctx):
        panel = types.Object()
        grid = panel.grid('grid')
        grid.str('message', view=types.View(space=3))
        grid.btn('btn', label="+1", on_click=self.on_click)
        grid.btn('notify_btn', label="Notify", on_click=self.on_click_notify)
        return types.Property(panel)
    def on_click(self, ctx):
        grid = ctx.panel.state.grid or {}
        current_count = grid.get("count", 0)
        count = current_count + 1
        message = f"The count is {count}"
        ctx.panel.state.grid = {"count": count, "message": message}
    def on_click_notify(self, ctx):
        ctx.ops.notify(ctx.panel.state.grid.get("message", "No message"))



class TodoListPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelOperatorConfig(
            name="todo_list_panel",
            label="Example: Todo List"
        )
    
    def on_load(self, ctx):
        print("Panel loaded")
        ctx.panel.state.todos = [
            {"task": "Buy milk", "completed": False},
            {"task": "Walk the dog", "completed": True},
            {"task": "Do the dishes", "completed": False},
        ]

    def render(self, ctx):
        panel = types.Object()
        todo = types.Object()
        todo.bool('completed')
        todo.str('task')
        panel.list('todos', element_type=todo)
        panel.btn('clear_completed', label="Clear Completed", on_click=self.on_click_clear_complete)
        return types.Property(panel)

    def on_click_clear_complete(self, ctx):
        ctx.panel.state.todos = []
        # todos = ctx.panel.state.todos
        # ctx.panel.state.todos = [todo for todo in todos if not todo.get("completed", False)]

def register(p):
    p.register(IncCountPanel)
    p.register(TodoListPanel)
