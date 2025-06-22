import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import simpledialog
import sqlite3

class RegistrationApp:
    def __init__(self, master):
        self.master = master
        self.master.title("App")
        self.master.geometry("300x150")
        self.master.resizable(False, False)

        self.conn = sqlite3.connect('Extras/tournament_management.db')
        self.cursor = self.conn.cursor()
        print("Connection to database established")

        self.participant_count = 0
        self.team_count = 0
        self.max_participants = 40

        self.create_widgets()

    def create_widgets(self):
        # First Row: Label
        self.label = tk.Label(self.master, text="Registration Menu")
        self.label.pack()

        # Second Row: As Individual and As Team buttons next to each other
        individual_team_frame = tk.Frame(self.master)
        individual_team_frame.pack()

        self.button_individual = tk.Button(individual_team_frame, text="As Individual",
                                           command=self.register_individual)
        self.button_individual.pack(side=tk.LEFT)

        self.button_team = tk.Button(individual_team_frame, text="As Team", command=self.register_team)
        self.button_team.pack(side=tk.LEFT, padx=5)  # Adding horizontal padding between the buttons

        # Third Row: Complete registration button
        self.button_complete = tk.Button(self.master, text="Complete Registration",
                                         command=self.show_tournament_handling_window)
        self.button_complete.pack()

        # Fourth Row: Exit and Help buttons next to each other
        self.create_exit_help_buttons(self.master,
                                      "This menu allows you to register participants either as individuals or as part of a team for upcoming events. Click As Individual to register participants individually or As Team to register participants as part of a team. Once all registrations are complete, click Complete Registration to proceed.",
                                      is_first_window=True)

    def show_help(self, help_message):
        self.msgbox = tk.messagebox.showinfo(title="Help", message=help_message)

    def create_exit_help_buttons(self, parent, help_message, is_first_window=False):
        exit_help_frame = tk.Frame(parent)
        exit_help_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)  # Padding at the bottom

        if is_first_window:
            button_text = "Exit"
            button_command = self.confirm_exit
        else:
            button_text = "Back"
            button_command = parent.destroy  # Close current window

        self.button_exit = tk.Button(exit_help_frame, text=button_text, command=button_command)
        self.button_exit.pack(side=tk.LEFT, padx=5)  # Align to left and add horizontal padding

        self.button_help = tk.Button(exit_help_frame, text="Help", command=lambda: self.show_help(help_message))
        self.button_help.pack(side=tk.RIGHT, padx=5)  # Align to right and add horizontal padding

    def confirm_exit(self):
        if messagebox.askyesno("Confirmation", "Are you sure you want to exit?"):
            self.master.destroy()

    def load_events(self, registration_type):
        self.cursor.execute("SELECT EventID, EventName FROM Events WHERE EventType=?", (registration_type,))
        events = {str(row[0]): row[1] for row in self.cursor.fetchall()}
        return events

    def register_individual(self):
        if self.participant_count < self.max_participants:
            individual_registration_window = tk.Toplevel(self.master)
            individual_registration_window.title("Individual Registration")
            individual_registration_window.geometry("250x350")
            individual_registration_window.resizable(False, False)

            self.predefined_events = self.load_events("Individual")

            label_info = tk.Label(individual_registration_window, text="Enter participant nickname:")
            label_info.pack()

            self.entry_info = tk.Entry(individual_registration_window)
            self.entry_info.pack()

            label_events_info = tk.Label(individual_registration_window, text="Select events:")
            label_events_info.pack()

            self.selected_events = []
            self.event_checkboxes = {}
            for event_id, event_name in self.predefined_events.items():
                var = tk.BooleanVar()
                checkbox = tk.Checkbutton(individual_registration_window, text=event_name, variable=var)
                checkbox.pack(anchor=tk.W)
                self.event_checkboxes[event_id] = (var, event_name)

            submit_button = tk.Button(individual_registration_window, text="Submit", command=self.submit_individual)
            submit_button.pack()

            clear_button = tk.Button(individual_registration_window, text="Clear All Fields", command=self.clear_individual_fields)
            clear_button.pack()

            self.create_exit_help_buttons(individual_registration_window,
                                          "In this window, you can register individual participants for events. Enter the participant's nickname, select the events they want to participate in, and click Submit to register them. You can also click Clear All Fields to reset the form. If you need assistance, click Help.",
                                          is_first_window=False)

        else:
            messagebox.showinfo("Registration Limit", "Maximum participant limit reached.")

    def submit_individual(self):
        info = self.entry_info.get().strip()
        if not info:
            messagebox.showerror("Error", "Please fill in the participant nickname.")
            return

        self.cursor.execute("SELECT COUNT(*) FROM Participants WHERE Name=?", (info,))
        participant_count = self.cursor.fetchone()[0]
        if participant_count > 0:
            messagebox.showerror("Error", "Participant nickname already exists. Please choose a different one.")
            return

        # Check if at least one event is selected
        if not any(var.get() for var, _ in self.event_checkboxes.values()):
            messagebox.showerror("Error", "Please select at least one event.")
            return

        # Check if the maximum number of individual participants has been reached
        self.cursor.execute("SELECT COUNT(*) FROM Participants WHERE TeamID IS NULL")
        individual_participant_count = self.cursor.fetchone()[0]
        if individual_participant_count >= 20:
            messagebox.showerror("Error", "Maximum individual participant limit reached.")
            return

        # Insert the participant into the Participants table
        self.cursor.execute("INSERT INTO Participants (Name) VALUES (?)", (info,))
        participant_id = self.cursor.lastrowid

        for event_id, (var, event_name) in self.event_checkboxes.items():
            if var.get():
                # Register the participant for each selected event in the EventParticipants table
                self.cursor.execute(
                    "INSERT INTO EventParticipants (EventID, ParticipantID, TeamID, PointsEarned) VALUES (?, ?, ?, ?)",
                    (event_id, participant_id, None, 0))

        self.conn.commit()

        messagebox.showinfo("Registration Successful", "Participant successfully registered for selected events.")

        # Clear the selected events list
        self.selected_events = []

    def clear_individual_fields(self):
        self.entry_info.delete(0, tk.END)
        for var, _ in self.event_checkboxes.values():
            var.set(False)

    def register_team(self):
        team_registration_window = tk.Toplevel(self.master)
        team_registration_window.title("Team Registration")
        team_registration_window.geometry("350x500")
        team_registration_window.resizable(False, False)

        self.predefined_events = self.load_events("Team-based")

        label_team_name = tk.Label(team_registration_window, text="Enter desired team name:")
        label_team_name.pack()

        self.entry_team_name = tk.Entry(team_registration_window)
        self.entry_team_name.pack()

        label_member_name = tk.Label(team_registration_window, text="Enter nicknames for each member:")
        label_member_name.pack()

        member_frame = tk.Frame(team_registration_window)
        member_frame.pack()

        # Create an empty list to store entry widgets for team members
        self.team_members = []

        # Labels and entry fields for team members
        for i in range(5):
            label_member = tk.Label(member_frame, text=f"Member {i + 1}:")
            label_member.grid(row=i, column=0, padx=5)  # Place the label on the left
            entry_member = tk.Entry(member_frame)
            entry_member.grid(row=i, column=1)  # Place the entry field next to the label
            self.team_members.append(entry_member)  # Append the entry widget to the list

        label_events_info = tk.Label(team_registration_window, text="Select events:")
        label_events_info.pack()

        self.selected_events = []
        self.event_checkboxes = {}
        for event_id, event_name in self.predefined_events.items():
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(team_registration_window, text=event_name, variable=var)
            checkbox.pack(anchor=tk.W)
            self.event_checkboxes[event_id] = (var, event_name)

        submit_button = tk.Button(team_registration_window, text="Submit", command=self.submit_team)
        submit_button.pack()

        clear_button = tk.Button(team_registration_window, text="Clear All Fields", command=self.clear_team_fields)
        clear_button.pack()

        # Fifth Row: Exit and Help buttons next to each other
        self.create_exit_help_buttons(team_registration_window,
                                      "This window allows you to register teams for events. Enter a team name and the nicknames of team members, select the events they want to participate in, and click Submit to register the team. You can also click Clear All Fields to reset the form. If you need assistance, click Help.",
                                      is_first_window=False)

    def submit_team(self):
        team_name = self.entry_team_name.get().strip()
        if not team_name:
            messagebox.showerror("Error", "Please fill in the team name.")
            return

        self.cursor.execute("SELECT COUNT(*) FROM Teams WHERE TeamName=?", (team_name,))
        participant_count = self.cursor.fetchone()[0]
        if participant_count > 0:
            messagebox.showerror("Error", "Team name already exists. Please choose a different one.")
            return

        # Check if at least one member name is provided
        if not any(entry_member.get().strip() for entry_member in self.team_members):
            messagebox.showerror("Error", "Please fill in at least one member name.")
            return

        # Check if at least one event is selected
        if not any(var.get() for var, _ in self.event_checkboxes.values()):
            messagebox.showerror("Error", "Please select at least one event.")
            return

        # Check if the maximum number of teams has been reached
        self.cursor.execute("SELECT COUNT(*) FROM Teams")
        team_count = self.cursor.fetchone()[0]
        if team_count >= 4:
            messagebox.showerror("Error", "Maximum team limit reached.")
            return

        # Insert the team into the Teams table
        self.cursor.execute("INSERT INTO Teams (TeamName) VALUES (?)", (team_name,))
        team_id = self.cursor.lastrowid

        # Insert team members into the Participants table
        for entry_member in self.team_members:
            member_name = entry_member.get().strip()
            if member_name:
                self.cursor.execute("INSERT INTO Participants (Name, TeamID) VALUES (?, ?)", (member_name, team_id))

        # Insert the team into the EventParticipants table for each selected event
        for event_id, (var, _) in self.event_checkboxes.items():
            if var.get():
                self.cursor.execute(
                    "INSERT INTO EventParticipants (EventID, TeamID, PointsEarned) VALUES (?, ?, ?)",
                    (event_id, team_id, 0)
                )

        self.conn.commit()

        # Inform the user about successful team registration
        messagebox.showinfo("Registration Successful", "Team successfully registered.")

    def clear_team_fields(self):
        self.entry_team_name.delete(0, tk.END)
        for entry in self.team_members:
            entry.delete(0, tk.END)
        for var, _ in self.event_checkboxes.values():
            var.set(False)

    def show_tournament_handling_window(self):
        # Display a confirmation dialog
        if messagebox.askyesno("Confirmation",
                               "Are you sure you completed registration process and want to be transferred to the tournament handling section?"):
            tournament_handling_window = tk.Toplevel(self.master)
            tournament_handling_window.title("Tournament Handling")
            tournament_handling_window.geometry("1000x600")

            # Create a custom style to add cell borders
            style = ttk.Style()
            style.configure("Treeview", rowheight=25)
            style.configure("Treeview.Heading", font=(None, 12, "bold"))  # Set font size and weight for headings

            # Create the outer notebook (for individual and team events)
            outer_notebook = ttk.Notebook(tournament_handling_window)
            outer_notebook.pack(fill=tk.BOTH, expand=True)

            # Create tabs for individual events and team events
            individual_tab = tk.Frame(outer_notebook)
            team_tab = tk.Frame(outer_notebook)
            scoreboard_tab = tk.Frame(outer_notebook)
            outer_notebook.add(individual_tab, text="Individual Events")
            outer_notebook.add(team_tab, text="Team Events")
            outer_notebook.add(scoreboard_tab, text="Tournament Scoreboard")

            individual_notebook = ttk.Notebook(individual_tab)
            individual_notebook.pack(fill=tk.BOTH, expand=True)

            # Retrieve individual events from the database
            self.cursor.execute("SELECT EventID, EventName FROM Events WHERE EventType='Individual'")
            individual_events = self.cursor.fetchall()

            # Create tabs for individual events
            for event in individual_events:
                event_id, event_name = event
                individual_event_tab = tk.Frame(individual_notebook)
                individual_notebook.add(individual_event_tab, text=event_name)

                # Create a treeview widget for displaying participants and their points
                tree = ttk.Treeview(individual_event_tab, columns=("Rank", "ID", "Participant", "Points"),
                                    show="headings",
                                    style="Treeview")
                tree.heading("Rank", text="Rank")
                tree.heading("ID", text="ID")
                tree.heading("Participant", text="Participant")
                tree.heading("Points", text="Points")
                tree.pack(fill=tk.BOTH, expand=True)

                # Retrieve participants and their points for the current event from the database
                self.cursor.execute("""
                    SELECT 
                        ep.ParticipantID, 
                        COALESCE(p.Name, t.TeamName) AS Name, 
                        ep.PointsEarned
                    FROM 
                        EventParticipants ep
                    LEFT JOIN 
                        Participants p ON p.ParticipantID = ep.ParticipantID
                    LEFT JOIN 
                        Teams t ON t.TeamID = ep.TeamID
                    WHERE 
                        ep.EventID = ?
                    ORDER BY 
                        ep.PointsEarned DESC
                """, (event_id,))
                participants = self.cursor.fetchall()

                # Insert participants and their points into the treeview
                for rank, participant in enumerate(participants, start=1):
                    tree.insert("", "end", values=(rank, participant[0], participant[1], participant[2]),
                                tags=('centered',))

                # Center the text in all columns
                for col in tree["columns"]:
                    tree.heading(col, anchor="center")
                    tree.column(col, anchor="center")

                # Bind the edit_points method to the treeview for individual events
                tree.bind('<Double-1>',
                          lambda event, tree=tree, event_id=event_id, event_type='Individual': self.edit_points(event,
                                                                                                                tree,
                                                                                                                event_id,
                                                                                                                event_type))

            # Create a notebook for team events
            team_notebook = ttk.Notebook(team_tab)
            team_notebook.pack(fill=tk.BOTH, expand=True)

            # Retrieve team events from the database
            self.cursor.execute("SELECT EventID, EventName FROM Events WHERE EventType='Team-based'")
            team_events = self.cursor.fetchall()

            # Create tabs for team events
            for event in team_events:
                event_id, event_name = event
                team_event_tab = tk.Frame(team_notebook)
                team_notebook.add(team_event_tab, text=event_name)

                # Create a treeview widget for displaying teams and their points
                tree = ttk.Treeview(team_event_tab, columns=("Rank", "ID", "Team", "Points"), show="headings",
                                    style="Treeview")
                tree.heading("Rank", text="Rank")
                tree.heading("ID", text="ID")
                tree.heading("Team", text="Team")
                tree.heading("Points", text="Points")
                tree.pack(fill=tk.BOTH, expand=True)

                # Retrieve teams and their points for the current event from the database
                self.cursor.execute("""
                            SELECT 
                                ep.TeamID, 
                                t.TeamName, 
                                SUM(ep.PointsEarned) AS TotalPoints
                            FROM 
                                Teams t
                            INNER JOIN 
                                EventParticipants ep ON t.TeamID = ep.TeamID
                            WHERE 
                                ep.EventID = ?
                            GROUP BY 
                                ep.TeamID, t.TeamName
                            ORDER BY 
                                TotalPoints DESC
                        """, (event_id,))
                teams = self.cursor.fetchall()

                # Insert teams and their points into the treeview
                for rank, team in enumerate(teams, start=1):
                    tree.insert("", "end", values=(rank, team[0], team[1], team[2]), tags=('centered',))

                # Center the text in all columns
                for col in tree["columns"]:
                    tree.heading(col, anchor="center")
                    tree.column(col, anchor="center")

                # Bind the edit_points method to the treeview for team events
                tree.bind('<Double-1>',
                          lambda event, tree=tree, event_id=event_id, event_type='Team-based': self.edit_points(event,
                                                                                                                tree,
                                                                                                                event_id,
                                                                                                                event_type))

            self.populate_scoreboard_tab(scoreboard_tab)

            # Add Exit and Help buttons
            self.create_exit_help_buttons(tournament_handling_window,
                                          "This window displays information about individual and team events, including participants and their points. You can edit the points for each participant or team by double-clicking on their entry. The Tournament Scoreboard tab shows the overall standings of participants and teams based on their total points. If you need assistance, click Help.",
                                          is_first_window=False)

            # Apply custom style to center text in all cells
            tournament_handling_window.mainloop()

    def populate_scoreboard_tab(self, scoreboard_tab):
        # Create a treeview widget for displaying the tournament scoreboard
        tree = ttk.Treeview(scoreboard_tab, columns=("Rank", "Team/Participant", "Total Points"), show="headings",
                            style="Treeview")
        tree.heading("Rank", text="Rank")
        tree.heading("Team/Participant", text="Team/Participant")
        tree.heading("Total Points", text="Total Points")
        tree.pack(fill=tk.BOTH, expand=True)

        # Retrieve participants and their total points across all events from the database
        self.cursor.execute("""
            SELECT
                COALESCE(p.TeamID, 'Individual') AS TeamOrIndividual,
                COALESCE(t.TeamName, p.Name) AS TeamOrParticipant,
                COALESCE(SUM(ep.PointsEarned), 
                         (SELECT SUM(ep2.PointsEarned) 
                          FROM EventParticipants ep2
                          WHERE ep2.TeamID = p.TeamID)) AS TotalPoints
            FROM Participants p
            LEFT JOIN Teams t ON p.TeamID = t.TeamID
            LEFT JOIN EventParticipants ep ON p.ParticipantID = ep.ParticipantID
            GROUP BY TeamOrIndividual, TeamOrParticipant
            Order BY TotalPoints DESC
        """)
        participants = self.cursor.fetchall()

        # Insert participants and their total points into the treeview
        for rank, participant in enumerate(participants, start=1):
            tree.insert("", "end", values=(rank, participant[1], participant[2]), tags=('centered',))

        # Center the text in all columns
        for col in tree["columns"]:
            tree.heading(col, anchor="center")
            tree.column(col, anchor="center")

    def edit_points(self, event, tree, event_id, event_type):
        # Identify the item clicked on
        item = tree.selection()[0]

        # Retrieve current points value, participant/team ID, and rank
        current_points = tree.item(item, "values")[3]
        if event_type == 'Individual':
            participant_id = tree.item(item, "values")[1]
        elif event_type == 'Team-based':
            team_id = tree.item(item, "values")[1]
        rank = tree.item(item, "values")[0]

        # Prompt the user to input new points value
        new_points = simpledialog.askinteger("Edit Points", f"Enter new points for {tree.item(item, 'values')[2]}:",
                                             initialvalue=current_points)

        # If the user cancels or inputs invalid value, return
        if new_points is None or new_points == '':
            return

        if new_points is None or new_points == '' or new_points < 0:
            messagebox.showerror("Error", "Invalid points value. Please enter a non-negative integer.")
            return

        # Update the points value in the database
        if event_type == 'Individual':
            self.cursor.execute("""
                UPDATE EventParticipants 
                SET PointsEarned = ? 
                WHERE EventID = ? 
                AND ParticipantID = ?
            """, (new_points, event_id, participant_id))
        elif event_type == 'Team-based':
            self.cursor.execute("""
                UPDATE EventParticipants 
                SET PointsEarned = ? 
                WHERE EventID = ? 
                AND TeamID = ?
            """, (new_points, event_id, team_id))

        self.conn.commit()

        # Update the displayed value in the treeview
        tree.item(item, values=(rank, tree.item(item, "values")[1], tree.item(item, "values")[2], new_points))

        # Reorder participants in the treeview based on the updated points
        self.refresh_treeview(tree, event_id, event_type)

    def refresh_treeview(self, tree, event_id, event_type):
        # Clear the existing items in the treeview
        tree.delete(*tree.get_children())

        # Retrieve participants and their points for the current event from the database
        if event_type == 'Individual':
            query = """
                SELECT 
                    ep.ParticipantID, 
                    COALESCE(p.Name, t.TeamName) AS Name, 
                    ep.PointsEarned
                FROM 
                    EventParticipants ep
                LEFT JOIN 
                    Participants p ON p.ParticipantID = ep.ParticipantID
                LEFT JOIN 
                    Teams t ON t.TeamID = ep.TeamID
                WHERE 
                    ep.EventID = ?
                ORDER BY 
                    ep.PointsEarned DESC
            """
        elif event_type == 'Team-based':
            query = """
                SELECT 
                    ep.TeamID, 
                    t.TeamName, 
                    ep.PointsEarned
                FROM 
                    Teams t
                INNER JOIN 
                    EventParticipants ep ON t.TeamID = ep.TeamID
                WHERE 
                    ep.EventID = ?
                ORDER BY 
                    ep.PointsEarned DESC
            """

        self.cursor.execute(query, (event_id,))
        participants = self.cursor.fetchall()

        # Insert participants and their points into the treeview
        for rank, participant in enumerate(participants, start=1):
            tree.insert("", "end", values=(rank, participant[0], participant[1], participant[2]), tags=('centered',))

        # Center the text in all columns
        for col in tree["columns"]:
            tree.heading(col, anchor="center")
            tree.column(col, anchor="center")


if __name__ == "__main__":
    root = tk.Tk()
    app = RegistrationApp(root)
    root.mainloop()
