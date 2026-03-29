import discord
from discord import app_commands
from discord.ui import View, Button
import os

# Get token from Railway environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

class TicketBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.ticket_counter = 0

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Failed to sync commands: {e}')

bot = TicketBot()

# Ticket Panel View (Create Ticket Button)
class TicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="🎫 Create Ticket", 
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        bot.ticket_counter += 1
        ticket_number = bot.ticket_counter
        
        # Create ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}"
        )
        
        # Create ticket view with Close and Claim buttons
        ticket_view = TicketView()
        
        embed = discord.Embed(
            title=f"Ticket #{ticket_number}",
            description=f"Ticket created by {interaction.user.mention}\n\nSupport team will assist you shortly!",
            color=discord.Color.blue()
        )
        
        await ticket_channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=ticket_view
        )
        
        await interaction.response.send_message(
            f"✅ Ticket created: {ticket_channel.mention}", 
            ephemeral=True
        )

# Ticket View (Close and Claim Buttons)
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed_by = None
    
    @discord.ui.button(
        label="🔒 Close", 
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # Confirm close
        confirm_view = ConfirmCloseView()
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=confirm_view,
            ephemeral=True
        )

    @discord.ui.button(
        label="🙋 Claim", 
        style=discord.ButtonStyle.success,
        custom_id="claim_ticket"
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if self.claimed_by is not None:
            await interaction.response.send_message(
                f"This ticket is already claimed by {self.claimed_by.mention}!",
                ephemeral=True
            )
            return
        
        self.claimed_by = interaction.user
        
        # Update button to show claimed
        for child in self.children:
            if child.custom_id == "claim_ticket":
                child.label = f"✅ Claimed by @{interaction.user.name}"
                child.disabled = True
        
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(
            f"✅ Ticket claimed by {interaction.user.mention}"
        )

# Confirm Close View
class ConfirmCloseView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @discord.ui.button(label="Yes, Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete(reason=f"Closed by {interaction.user}")
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Close cancelled.", view=None)

# /panel command
@bot.tree.command(name="panel", description="Spawn a ticket panel")
@app_commands.default_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description="Click the button below to create a support ticket!",
        color=discord.Color.green()
    )
    
    view = TicketPanel()
    await interaction.response.send_message(embed=embed, view=view)

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        exit(1)
    bot.run(TOKEN)
