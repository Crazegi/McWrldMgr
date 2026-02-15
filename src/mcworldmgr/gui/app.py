from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from mcworldmgr.services import operations


def launch_gui() -> None:
    root = tk.Tk()
    root.title("Minecraft World Manager")
    root.geometry("980x760")
    App(root)
    root.mainloop()


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.event_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.saves_dir_var = tk.StringVar(value="")
        self.world_var = tk.StringVar(value="")
        self.world_path_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")

        self.backup_progress_var = tk.DoubleVar(value=0)
        self.backup_progress_total = 1
        self.backup_progress_text = tk.StringVar(value="0/0")

        self._build_header()
        self._build_tabs()
        self._build_footer()
        self.refresh_worlds()
        self._poll_events()

    def _build_header(self) -> None:
        frame = ttk.LabelFrame(self.root, text="World Selection")
        frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(frame, text="Saves dir override:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.saves_dir_var, width=70).grid(
            row=0, column=1, sticky="ew", padx=6, pady=6
        )
        ttk.Button(frame, text="Refresh Worlds", command=self.refresh_worlds).grid(
            row=0, column=2, sticky="e", padx=6, pady=6
        )

        ttk.Label(frame, text="Detected world:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.world_combo = ttk.Combobox(frame, textvariable=self.world_var, state="readonly", width=45)
        self.world_combo.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(frame, text="Manual world path/name:").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.world_path_var, width=70).grid(
            row=2, column=1, sticky="ew", padx=6, pady=6
        )

        frame.columnconfigure(1, weight=1)

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.inspect_tab = ttk.Frame(self.notebook)
        self.backup_tab = ttk.Frame(self.notebook)
        self.world_tab = ttk.Frame(self.notebook)
        self.gamerule_tab = ttk.Frame(self.notebook)
        self.player_tab = ttk.Frame(self.notebook)
        self.entity_tab = ttk.Frame(self.notebook)
        self.regions_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.inspect_tab, text="Inspect")
        self.notebook.add(self.backup_tab, text="Backup")
        self.notebook.add(self.world_tab, text="World")
        self.notebook.add(self.gamerule_tab, text="Gamerule")
        self.notebook.add(self.player_tab, text="Player")
        self.notebook.add(self.entity_tab, text="Entity")
        self.notebook.add(self.regions_tab, text="Regions")

        self._build_inspect_tab()
        self._build_backup_tab()
        self._build_world_tab()
        self._build_gamerule_tab()
        self._build_player_tab()
        self._build_entity_tab()
        self._build_regions_tab()

    def _build_footer(self) -> None:
        footer = ttk.Frame(self.root)
        footer.pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Label(footer, textvariable=self.status_var).pack(side=tk.LEFT)

    def _selected_world_arg(self) -> str:
        manual = self.world_path_var.get().strip()
        if manual:
            return manual
        selected = self.world_var.get().strip()
        if selected:
            return selected
        raise ValueError("Select a world or provide manual world path/name.")

    def _saves_dir(self) -> str | None:
        value = self.saves_dir_var.get().strip()
        return value or None

    def _confirm(self, message: str) -> bool:
        return bool(messagebox.askyesno("Confirm", message))

    def _confirm_write(self) -> bool:
        return bool(messagebox.askyesno("Confirm Write", "This will modify world data. Continue?"))

    def _ask_backup(self) -> bool:
        return bool(messagebox.askyesno("Backup", "Create backup before this write action?"))

    def _handle_error(self, error: Exception) -> None:
        self.status_var.set(f"Error: {error}")
        messagebox.showerror("Operation failed", str(error))

    def refresh_worlds(self) -> None:
        try:
            worlds = operations.list_world_refs(self._saves_dir())
            names = [w.name for w in worlds]
            self.world_combo["values"] = names
            if names and not self.world_var.get():
                self.world_var.set(names[0])
            self.status_var.set(f"Loaded {len(names)} world(s)")
        except Exception as exc:
            self._handle_error(exc)

    def _run_background(self, work: Callable[[Callable[[int, int, str], None]], object], done_event: str) -> None:
        def progress(current: int, total: int, label: str) -> None:
            self.event_queue.put(("progress", (current, total, label)))

        def runner() -> None:
            try:
                result = work(progress)
                self.event_queue.put((done_event, result))
            except Exception as exc:
                self.event_queue.put(("error", exc))

        threading.Thread(target=runner, daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.event_queue.get_nowait()
                if event == "progress":
                    current, total, label = payload  # type: ignore[misc]
                    self.backup_progress_total = max(total, 1)
                    self.backup_progress_var.set((current / self.backup_progress_total) * 100)
                    self.backup_progress_text.set(f"{current}/{total} {label}")
                elif event == "backup_created":
                    self.status_var.set(f"Backup created: {payload}")
                    messagebox.showinfo("Success", f"Backup created:\n{payload}")
                    self.refresh_backups()
                elif event == "backup_restored":
                    self.status_var.set("Backup restored")
                    messagebox.showinfo("Success", "Backup restored.")
                elif event == "error":
                    self._handle_error(payload)  # type: ignore[arg-type]
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _build_inspect_tab(self) -> None:
        ttk.Button(self.inspect_tab, text="Inspect World", command=self.on_inspect).pack(anchor="w", padx=8, pady=8)
        self.inspect_text = tk.Text(self.inspect_tab, height=24)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def on_inspect(self) -> None:
        try:
            info = operations.get_world_inspect_info(self._selected_world_arg(), self._saves_dir())
            lines = [
                f"World: {info['world_name']}",
                f"Path: {info['path']}",
                f"DataVersion: {info['data_version']}",
                f"LevelName: {info['level_name']}",
                f"Difficulty: {info['difficulty']}",
                f"GameType: {info['gametype']}",
                f"Time: {info['time']}",
                f"GameRules: {info['gamerules_count']}",
                f"Players: {info['players_count']}",
                f"Regions: {info['regions_count']}",
                f"Entity regions: {info['entity_regions_count']}",
            ]
            self.inspect_text.delete("1.0", tk.END)
            self.inspect_text.insert("1.0", "\n".join(lines))
            self.status_var.set("Inspect completed")
        except Exception as exc:
            self._handle_error(exc)

    def _build_backup_tab(self) -> None:
        frame = ttk.Frame(self.backup_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Create Backup", command=self.on_create_backup).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Refresh Backups", command=self.refresh_backups).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Restore Selected", command=self.on_restore_backup).pack(side=tk.LEFT, padx=4)

        self.backup_list = tk.Listbox(frame, height=12)
        self.backup_list.pack(fill=tk.X, pady=8)

        progress_frame = ttk.LabelFrame(frame, text="Progress")
        progress_frame.pack(fill=tk.X, pady=8)
        ttk.Progressbar(progress_frame, variable=self.backup_progress_var, maximum=100).pack(
            fill=tk.X, padx=6, pady=6
        )
        ttk.Label(progress_frame, textvariable=self.backup_progress_text).pack(anchor="w", padx=6, pady=(0, 6))

    def refresh_backups(self) -> None:
        try:
            backups = operations.list_backups_for_world(self._selected_world_arg(), self._saves_dir())
            self.backup_list.delete(0, tk.END)
            for name in backups:
                self.backup_list.insert(tk.END, name)
            self.status_var.set(f"Loaded {len(backups)} backup(s)")
        except Exception as exc:
            self._handle_error(exc)

    def on_create_backup(self) -> None:
        try:
            world_arg = self._selected_world_arg()
            if not self._confirm("Create backup now?"):
                return
            self.backup_progress_var.set(0)
            self.backup_progress_text.set("0/0")

            def work(progress: Callable[[int, int, str], None]) -> str:
                result = operations.create_backup_for_world(
                    world_arg,
                    self._saves_dir(),
                    confirm=lambda _: True,
                    progress=progress,
                )
                return str(result)

            self._run_background(work, "backup_created")
            self.status_var.set("Creating backup...")
        except Exception as exc:
            self._handle_error(exc)

    def on_restore_backup(self) -> None:
        try:
            selection = self.backup_list.curselection()
            if not selection:
                raise ValueError("Select a backup to restore.")
            backup_name = self.backup_list.get(selection[0])
            if not self._confirm("Restore selected backup? This will overwrite current world files."):
                return

            world_arg = self._selected_world_arg()
            self.backup_progress_var.set(0)
            self.backup_progress_text.set("0/0")

            def work(progress: Callable[[int, int, str], None]) -> str:
                operations.restore_backup_for_world(
                    world_arg,
                    backup_name,
                    self._saves_dir(),
                    confirm=lambda _: True,
                    progress=progress,
                )
                return backup_name

            self._run_background(work, "backup_restored")
            self.status_var.set("Restoring backup...")
        except Exception as exc:
            self._handle_error(exc)

    def _build_world_tab(self) -> None:
        form = ttk.LabelFrame(self.world_tab, text="Basic World Settings")
        form.pack(fill=tk.X, padx=8, pady=8)

        self.world_name_var = tk.StringVar()
        self.world_difficulty_var = tk.StringVar()
        self.world_gamemode_var = tk.StringVar()

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=self.world_name_var, width=40).grid(row=0, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(form, text="Difficulty:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(form, textvariable=self.world_difficulty_var, values=["", "peaceful", "easy", "normal", "hard"], state="readonly", width=20).grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(form, text="Gamemode:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(form, textvariable=self.world_gamemode_var, values=["", "survival", "creative", "adventure", "spectator"], state="readonly", width=20).grid(row=2, column=1, sticky="w", padx=4, pady=4)

        ttk.Button(form, text="Apply World Changes", command=self.on_world_set).grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=8)

        advanced = ttk.LabelFrame(self.world_tab, text="Advanced World Settings")
        advanced.pack(fill=tk.X, padx=8, pady=8)

        self.adv_time_var = tk.StringVar()
        self.adv_weather_var = tk.StringVar(value="")
        self.adv_weather_duration_var = tk.StringVar()
        self.adv_spawn_x_var = tk.StringVar()
        self.adv_spawn_y_var = tk.StringVar()
        self.adv_spawn_z_var = tk.StringVar()
        self.adv_border_cx_var = tk.StringVar()
        self.adv_border_cz_var = tk.StringVar()
        self.adv_border_size_var = tk.StringVar()
        self.adv_seed_var = tk.StringVar()
        self.adv_hardcore_var = tk.StringVar(value="")
        self.adv_allow_commands_var = tk.StringVar(value="")

        self._grid_entry(advanced, 0, "Time", self.adv_time_var)
        ttk.Label(advanced, text="Weather:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        ttk.Combobox(
            advanced,
            textvariable=self.adv_weather_var,
            values=["", "clear", "rain", "thunder"],
            state="readonly",
            width=27,
        ).grid(row=1, column=1, sticky="w", padx=4, pady=3)
        self._grid_entry(advanced, 2, "Weather Duration", self.adv_weather_duration_var)
        self._grid_entry(advanced, 3, "Spawn X", self.adv_spawn_x_var)
        self._grid_entry(advanced, 4, "Spawn Y", self.adv_spawn_y_var)
        self._grid_entry(advanced, 5, "Spawn Z", self.adv_spawn_z_var)
        self._grid_entry(advanced, 6, "Border Center X", self.adv_border_cx_var)
        self._grid_entry(advanced, 7, "Border Center Z", self.adv_border_cz_var)
        self._grid_entry(advanced, 8, "Border Size", self.adv_border_size_var)
        self._grid_entry(advanced, 9, "Seed", self.adv_seed_var)

        ttk.Label(advanced, text="Hardcore:").grid(row=10, column=0, sticky="w", padx=4, pady=3)
        ttk.Combobox(
            advanced,
            textvariable=self.adv_hardcore_var,
            values=["", "true", "false"],
            state="readonly",
            width=27,
        ).grid(row=10, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(advanced, text="Allow Commands:").grid(row=11, column=0, sticky="w", padx=4, pady=3)
        ttk.Combobox(
            advanced,
            textvariable=self.adv_allow_commands_var,
            values=["", "true", "false"],
            state="readonly",
            width=27,
        ).grid(row=11, column=1, sticky="w", padx=4, pady=3)

        ttk.Button(
            advanced,
            text="Apply Advanced Changes",
            command=self.on_world_advanced_set,
        ).grid(row=12, column=0, columnspan=2, sticky="w", padx=4, pady=8)

    def on_world_set(self) -> None:
        try:
            if not self._confirm_write():
                return
            operations.set_world_metadata(
                self._selected_world_arg(),
                self._saves_dir(),
                name=self.world_name_var.get().strip() or None,
                difficulty=self.world_difficulty_var.get().strip() or None,
                gamemode=self.world_gamemode_var.get().strip() or None,
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.status_var.set("World metadata updated")
            messagebox.showinfo("Success", "World metadata updated.")
        except Exception as exc:
            self._handle_error(exc)

    def on_world_advanced_set(self) -> None:
        try:
            if not self._confirm_write():
                return
            to_bool = lambda value: None if not value else value == "true"
            operations.set_world_advanced(
                self._selected_world_arg(),
                self._saves_dir(),
                time_value=self._to_int(self.adv_time_var.get()),
                weather=self.adv_weather_var.get().strip() or None,
                weather_duration=self._to_int(self.adv_weather_duration_var.get()),
                spawn_x=self._to_int(self.adv_spawn_x_var.get()),
                spawn_y=self._to_int(self.adv_spawn_y_var.get()),
                spawn_z=self._to_int(self.adv_spawn_z_var.get()),
                border_center_x=self._to_float(self.adv_border_cx_var.get()),
                border_center_z=self._to_float(self.adv_border_cz_var.get()),
                border_size=self._to_float(self.adv_border_size_var.get()),
                hardcore=to_bool(self.adv_hardcore_var.get().strip()),
                allow_commands=to_bool(self.adv_allow_commands_var.get().strip()),
                seed=self._to_int(self.adv_seed_var.get()),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.status_var.set("Advanced world settings updated")
            messagebox.showinfo("Success", "Advanced world settings updated.")
        except Exception as exc:
            self._handle_error(exc)

    def _build_gamerule_tab(self) -> None:
        form = ttk.Frame(self.gamerule_tab)
        form.pack(fill=tk.X, padx=8, pady=8)

        self.gamerule_name_var = tk.StringVar()
        self.gamerule_value_var = tk.StringVar()

        ttk.Label(form, text="Rule:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=self.gamerule_name_var, width=35).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(form, text="Value:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(form, textvariable=self.gamerule_value_var, width=35).grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Button(form, text="Set Gamerule", command=self.on_gamerule_set).grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=8)

    def on_gamerule_set(self) -> None:
        try:
            if not self._confirm_write():
                return
            rule = self.gamerule_name_var.get().strip()
            value = self.gamerule_value_var.get().strip()
            if not rule:
                raise ValueError("Gamerule name is required.")
            operations.set_gamerule(
                self._selected_world_arg(),
                rule,
                value,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.status_var.set("Gamerule updated")
            messagebox.showinfo("Success", f"Gamerule updated: {rule}={value}")
        except Exception as exc:
            self._handle_error(exc)

    def _build_player_tab(self) -> None:
        frame = ttk.Frame(self.player_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        ttk.Button(top, text="Load Players", command=self.refresh_players).pack(side=tk.LEFT, padx=4)

        self.player_uuid_var = tk.StringVar()
        ttk.Label(top, text="UUID:").pack(side=tk.LEFT, padx=(12, 4))
        self.player_combo = ttk.Combobox(top, textvariable=self.player_uuid_var, state="readonly", width=50)
        self.player_combo.pack(side=tk.LEFT, padx=4)

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=10)

        self.player_x = tk.StringVar()
        self.player_y = tk.StringVar()
        self.player_z = tk.StringVar()
        self.player_health = tk.StringVar()
        self.player_hunger = tk.StringVar()
        self.player_slot = tk.StringVar()

        self._grid_entry(form, 0, "X", self.player_x)
        self._grid_entry(form, 1, "Y", self.player_y)
        self._grid_entry(form, 2, "Z", self.player_z)
        self._grid_entry(form, 3, "Health", self.player_health)
        self._grid_entry(form, 4, "Hunger", self.player_hunger)
        self._grid_entry(form, 5, "Slot", self.player_slot)

        actions = ttk.Frame(frame)
        actions.pack(anchor="w", padx=4, pady=6)
        ttk.Button(actions, text="Apply Player Changes", command=self.on_player_set).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Kill Player", command=self.on_player_kill).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Delete Player Data", command=self.on_player_delete).pack(side=tk.LEFT, padx=3)

    def _grid_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=variable, width=30).grid(row=row, column=1, sticky="w", padx=4, pady=3)

    def refresh_players(self) -> None:
        try:
            players = operations.list_player_uuids(self._selected_world_arg(), self._saves_dir())
            self.player_combo["values"] = players
            if players:
                self.player_uuid_var.set(players[0])
            self.status_var.set(f"Loaded {len(players)} player(s)")
        except Exception as exc:
            self._handle_error(exc)

    def on_player_set(self) -> None:
        try:
            if not self._confirm_write():
                return
            uuid = self.player_uuid_var.get().strip()
            if not uuid:
                raise ValueError("Select a player UUID.")
            operations.set_player(
                self._selected_world_arg(),
                uuid,
                self._saves_dir(),
                x=self._to_float(self.player_x.get()),
                y=self._to_float(self.player_y.get()),
                z=self._to_float(self.player_z.get()),
                health=self._to_float(self.player_health.get()),
                hunger=self._to_int(self.player_hunger.get()),
                slot=self._to_int(self.player_slot.get()),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.status_var.set("Player updated")
            messagebox.showinfo("Success", "Player updated.")
        except Exception as exc:
            self._handle_error(exc)

    def on_player_kill(self) -> None:
        try:
            uuid = self.player_uuid_var.get().strip()
            if not uuid:
                raise ValueError("Select a player UUID.")
            if not self._confirm("Kill selected player (set health to 0)?"):
                return
            operations.kill_player(
                self._selected_world_arg(),
                uuid,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.status_var.set("Player killed")
            messagebox.showinfo("Success", "Player marked as dead.")
        except Exception as exc:
            self._handle_error(exc)

    def on_player_delete(self) -> None:
        try:
            uuid = self.player_uuid_var.get().strip()
            if not uuid:
                raise ValueError("Select a player UUID.")
            if not self._confirm("Delete selected player data file?"):
                return
            operations.delete_player(
                self._selected_world_arg(),
                uuid,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.refresh_players()
            self.status_var.set("Player data deleted")
            messagebox.showinfo("Success", "Player data deleted.")
        except Exception as exc:
            self._handle_error(exc)

    def _build_entity_tab(self) -> None:
        frame = ttk.Frame(self.entity_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        ttk.Button(top, text="Load Entity Regions", command=self.refresh_entity_regions).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Delete Selected", command=self.on_delete_entity_region).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Delete All", command=self.on_delete_all_entity_regions).pack(side=tk.LEFT, padx=4)

        self.entity_list = tk.Listbox(frame, height=16)
        self.entity_list.pack(fill=tk.BOTH, expand=True, pady=8)

        queue_box = ttk.LabelFrame(frame, text="Queue Entity Commands")
        queue_box.pack(fill=tk.X, pady=8)

        self.queue_entity_id_var = tk.StringVar(value="minecraft:zombie")
        self.queue_x_var = tk.StringVar(value="0")
        self.queue_y_var = tk.StringVar(value="64")
        self.queue_z_var = tk.StringVar(value="0")
        self.queue_nbt_var = tk.StringVar()
        self.queue_selector_var = tk.StringVar(value="@e[type=minecraft:zombie]")

        ttk.Label(queue_box, text="Entity ID:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_entity_id_var, width=26).grid(row=0, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(queue_box, text="X:").grid(row=0, column=2, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_x_var, width=8).grid(row=0, column=3, sticky="w", padx=4, pady=3)
        ttk.Label(queue_box, text="Y:").grid(row=0, column=4, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_y_var, width=8).grid(row=0, column=5, sticky="w", padx=4, pady=3)
        ttk.Label(queue_box, text="Z:").grid(row=0, column=6, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_z_var, width=8).grid(row=0, column=7, sticky="w", padx=4, pady=3)

        ttk.Label(queue_box, text="NBT suffix (optional):").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_nbt_var, width=72).grid(
            row=1, column=1, columnspan=7, sticky="w", padx=4, pady=3
        )

        ttk.Label(queue_box, text="Kill selector:").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(queue_box, textvariable=self.queue_selector_var, width=72).grid(
            row=2, column=1, columnspan=7, sticky="w", padx=4, pady=3
        )

        ttk.Button(queue_box, text="Queue Summon Command", command=self.on_queue_summon).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4, pady=6
        )
        ttk.Button(queue_box, text="Queue Kill Command", command=self.on_queue_kill).grid(
            row=3, column=2, columnspan=2, sticky="w", padx=4, pady=6
        )

    def refresh_entity_regions(self) -> None:
        try:
            files = operations.list_entity_regions(self._selected_world_arg(), self._saves_dir())
            self.entity_list.delete(0, tk.END)
            for name in files:
                self.entity_list.insert(tk.END, name)
            self.status_var.set(f"Loaded {len(files)} entity region file(s)")
        except Exception as exc:
            self._handle_error(exc)

    def on_delete_entity_region(self) -> None:
        try:
            selection = self.entity_list.curselection()
            if not selection:
                raise ValueError("Select an entity region file.")
            name = self.entity_list.get(selection[0])
            if not self._confirm("Delete selected entity region file?"):
                return
            operations.delete_entity_region(
                self._selected_world_arg(),
                name,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.refresh_entity_regions()
            self.status_var.set(f"Deleted entity region: {name}")
        except Exception as exc:
            self._handle_error(exc)

    def on_delete_all_entity_regions(self) -> None:
        try:
            if not self._confirm("Delete ALL entity region files?"):
                return
            count = operations.delete_all_entity_regions(
                self._selected_world_arg(),
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.refresh_entity_regions()
            self.status_var.set(f"Deleted {count} entity region file(s)")
            messagebox.showinfo("Success", f"Deleted {count} entity region file(s).")
        except Exception as exc:
            self._handle_error(exc)

    def on_queue_summon(self) -> None:
        try:
            path = operations.queue_summon_entity(
                self._selected_world_arg(),
                self.queue_entity_id_var.get().strip(),
                float(self.queue_x_var.get().strip()),
                float(self.queue_y_var.get().strip()),
                float(self.queue_z_var.get().strip()),
                self.queue_nbt_var.get().strip() or None,
                self._saves_dir(),
            )
            self.status_var.set(f"Summon command queued: {path}")
            messagebox.showinfo(
                "Queued",
                f"Command added to:\n{path}\n\nRun commands in Minecraft with /function or copy them manually.",
            )
        except Exception as exc:
            self._handle_error(exc)

    def on_queue_kill(self) -> None:
        try:
            selector = self.queue_selector_var.get().strip()
            if not selector:
                raise ValueError("Kill selector is required.")
            path = operations.queue_kill_entities(
                self._selected_world_arg(),
                selector,
                self._saves_dir(),
            )
            self.status_var.set(f"Kill command queued: {path}")
            messagebox.showinfo(
                "Queued",
                f"Command added to:\n{path}\n\nRun commands in Minecraft with /function or copy them manually.",
            )
        except Exception as exc:
            self._handle_error(exc)

    def _build_regions_tab(self) -> None:
        frame = ttk.Frame(self.regions_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        ttk.Button(top, text="Load Regions", command=self.refresh_regions).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Delete Selected", command=self.on_delete_region).pack(side=tk.LEFT, padx=4)

        self.region_list = tk.Listbox(frame, height=14)
        self.region_list.pack(fill=tk.BOTH, expand=True, pady=8)

        reset = ttk.LabelFrame(frame, text="Reset Chunk (deletes parent region file)")
        reset.pack(fill=tk.X, pady=6)
        self.chunk_x_var = tk.StringVar()
        self.chunk_z_var = tk.StringVar()
        ttk.Label(reset, text="Chunk X:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(reset, textvariable=self.chunk_x_var, width=14).grid(row=0, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(reset, text="Chunk Z:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(reset, textvariable=self.chunk_z_var, width=14).grid(row=0, column=3, sticky="w", padx=4, pady=4)
        ttk.Button(reset, text="Reset Chunk", command=self.on_reset_chunk).grid(row=0, column=4, sticky="w", padx=4, pady=4)

    def refresh_regions(self) -> None:
        try:
            files = operations.list_region_files(self._selected_world_arg(), self._saves_dir())
            self.region_list.delete(0, tk.END)
            for name in files:
                self.region_list.insert(tk.END, name)
            self.status_var.set(f"Loaded {len(files)} region file(s)")
        except Exception as exc:
            self._handle_error(exc)

    def on_delete_region(self) -> None:
        try:
            selection = self.region_list.curselection()
            if not selection:
                raise ValueError("Select a region file.")
            name = self.region_list.get(selection[0])
            if not self._confirm("Delete selected region file?"):
                return
            operations.delete_region(
                self._selected_world_arg(),
                name,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.refresh_regions()
            self.status_var.set(f"Deleted region: {name}")
        except Exception as exc:
            self._handle_error(exc)

    def on_reset_chunk(self) -> None:
        try:
            if not self._confirm("Reset chunk by deleting parent region file?"):
                return
            chunk_x = self._require_int(self.chunk_x_var.get(), "Chunk X")
            chunk_z = self._require_int(self.chunk_z_var.get(), "Chunk Z")
            region_name = operations.reset_chunk(
                self._selected_world_arg(),
                chunk_x,
                chunk_z,
                self._saves_dir(),
                confirm=lambda _: self._confirm("World lock found. Continue anyway?"),
                backup_before_write=self._ask_backup(),
            )
            self.refresh_regions()
            self.status_var.set(f"Chunk reset via deleted region: {region_name}")
            messagebox.showinfo("Success", f"Deleted region: {region_name}")
        except Exception as exc:
            self._handle_error(exc)

    def _to_float(self, value: str) -> float | None:
        value = value.strip()
        if not value:
            return None
        return float(value)

    def _to_int(self, value: str) -> int | None:
        value = value.strip()
        if not value:
            return None
        return int(value)

    def _require_int(self, value: str, field_name: str) -> int:
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} is required.")
        return int(value)
