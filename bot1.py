import discord
from discord.ext import commands
from discord.ui import View, Select
import os

TOKEN = "MTQwMjQ4NTg1Nzk2OTExNTIyOA.GKMzIt.vlvgAFRRxhv1Lq-mh_MBIqVC65C-xbA91i9TlQ"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

ticket_count = 0  # Counter for ticket numbering
ticket_channels = set()  # Track ticket channel IDs


class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="General Support",
                description="Get help from staff",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Prize Redemption",
                description="Redeem your prizes",
                emoji="🎁"
            )
        ]
        super().__init__(
            placeholder="Browse through ticket options",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        global ticket_count
        ticket_count += 1
        ticket_number = str(ticket_count).zfill(3)

        category_name = self.values[0]
        guild = interaction.guild

        # Check if category exists
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(name=category_name)

        # Create ticket channel
        channel = await category.create_text_channel(f"ticket-{ticket_number}")
        ticket_channels.add(channel.id)  # Store channel ID

        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(interaction.user, view_channel=True, send_messages=True)

        await channel.send(f"{interaction.user.mention}, your ticket has been created.")

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


@bot.command()
async def ticketpanel(ctx):
    embed = discord.Embed(
        title="Tickets",
        description=(
            "Use the selection menu below to navigate through ticket options.\n\n"
            "**Warnings:**\n"
            "• Don't create a ticket for trolling purposes, such behavior will result in consequences.\n"
            "• Tickets with no response within 24 hours will be closed.\n"
            "• Ensure that you provide evidence when reporting a rule violation.\n"
            "• Respect staff members, avoid pinging them, and be patient while awaiting support.\n"
            "• Refrain from discussing matters that require a different type of ticket.\n"
            "• Always read everything carefully before taking action. Not reading something is not an excuse.\n"
            "• Always check your invites before opening a ticket."
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    ch = ctx.channel
    is_ticket = False

    # Check topic marker
    if ch.topic and isinstance(ch.topic, str) and ch.topic.startswith("ticket:"):
        is_ticket = True

    # Or check category name
    if not is_ticket and ch.category and ch.category.name in ("General Support", "Prize Redemption"):
        is_ticket = True

    if not is_ticket:
        return await ctx.send("This command can only be used inside a ticket channel.")

    category = ch.category
    await ctx.send("Closing ticket...")
    await ch.delete()

    # Delete category if empty
    if category and len(category.channels) == 0:
        try:
            await category.delete()
        except Exception:
            pass

# =====================
# Verified & Unverified Commands
# =====================

@bot.command()
@commands.has_permissions(manage_channels=True)  # Mods & Admins
async def verified(ctx, number: int):
    """
    Usage: .verified <even number>
    Example: .verified 2 -> ✅ | verified 750t
             .verified 4 -> ✅ | verified 1500t
             Works with any even number.
    """
    if number <= 0 or number % 2 != 0:
        return await ctx.send("❌ Please provide an **even positive number**.")

    ticket_amount = (number // 2) * 750
    new_name = f"✅ | verified {ticket_amount}t"

    try:
        await ctx.channel.edit(name=new_name)
        await ctx.send(f"✅ Channel renamed to `{new_name}`")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to rename this channel.")
    except discord.HTTPException:
        await ctx.send("❌ Failed to rename the channel — something went wrong.")


@bot.command()
@commands.has_permissions(manage_channels=True)  # Mods & Admins
async def unverified(ctx):
    """Usage: .unverified -> ❌ | unverified"""
    new_name = "❌ | unverified"
    try:
        await ctx.channel.edit(name=new_name)
        await ctx.send(f"✅ Channel renamed to `{new_name}`")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to rename this channel.")
    except discord.HTTPException:
        await ctx.send("❌ Failed to rename the channel — something went wrong.")


# Error handler for permissions
@verified.error
@unverified.error
async def perms_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")


bot.run(TOKEN)
