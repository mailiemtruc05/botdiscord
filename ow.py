import discord
import asyncio
import os
import random
import re
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime, timedelta
from discord.ui import View, Button
from flask import Flask
from threading import Thread
from discord.ui import View, Select
from datetime import datetime, timedelta, timezone

load_dotenv()  # Đọc file .env
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="ow!", intents=intents)

MEM_ROLE_NAME = "MEM"
DEV_ROLE_NAME = "DEV"
CATEGORY_BUY = "Ticket Mua Hàng"
CATEGORY_SUPPORT = "Ticket Hỗ trợ/Bảo Hành"

# Lưu giveaway đang hoạt động hoặc có thể reroll
giveaway_views = {}          # Các giveaway đang diễn ra
ended_giveaways = {}         # Các giveaway đã kết thúc
VN_TZ = timezone(timedelta(hours=7))

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mua Hàng", style=discord.ButtonStyle.green, custom_id="buy")
    async def buy_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "mua-hang", CATEGORY_BUY)

    @discord.ui.button(label="Hỗ Trợ/Bảo Hành", style=discord.ButtonStyle.red, custom_id="support")
    async def support_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "ho-tro", CATEGORY_SUPPORT)

async def create_ticket(interaction: discord.Interaction, ticket_type: str, category_name: str):
    guild = interaction.guild
    member = interaction.user

    # Kiểm tra role MEM
    mem_role = discord.utils.get(guild.roles, name=MEM_ROLE_NAME)
    if mem_role not in member.roles:
        return await interaction.response.send_message("Bạn không có quyền mở ticket.", ephemeral=True)

    # Kiểm tra xem đã có ticket chưa
    for channel in guild.text_channels:
        if (channel.name.startswith("🎟┃mua-hang") or channel.name.startswith("🎟┃ho-tro")) and channel.topic == f"user:{member.id}":
            return await interaction.response.send_message("Bạn đã có một ticket đang mở.", ephemeral=True)

    # Tạo category nếu chưa có
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)

    # Tạo permission cho channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    dev_role = discord.utils.get(guild.roles, name=DEV_ROLE_NAME)
    if dev_role:
        overwrites[dev_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    # Tạo ticket channel và đánh dấu topic để dễ kiểm tra
    ticket_channel = await guild.create_text_channel(
        name=f"🎟┃{ticket_type}-{member.name}",
        category=category,
        overwrites=overwrites,
        topic=f"user:{member.id}"
    )

    await ticket_channel.send(
        f"{member.mention} đã mở ticket `{ticket_type.replace('-', ' ').title()}`. <@&1351227654782714040> sẽ hỗ trợ bạn."
    )

    embed = discord.Embed(
    title="Vui Lòng Chờ DEV Xíu Nhé.\nDEV Sẽ Trả Lời Nhanh Nhất Có Thể Ạ",
    color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

    await ticket_channel.send(embed=embed, view=CloseTicketView())


    await interaction.response.send_message(f"Ticket của bạn đã được tạo: {ticket_channel.mention}", ephemeral=True)


class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # ❌ XÓA DÒNG NÀY VÌ ĐÃ TẠO BUTTON BẰNG DECORATOR Ở DƯỚI
        # self.add_item(Button(label="Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket"))

    @discord.ui.button(label="Đóng Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        dev_role = discord.utils.get(interaction.guild.roles, name=DEV_ROLE_NAME)
        if dev_role not in interaction.user.roles:
            return await interaction.response.send_message("Bạn không có quyền đóng ticket này.", ephemeral=True)

        await interaction.response.send_message("Ticket sẽ bị đóng sau 5 giây...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def sendticket(ctx):
    embed = discord.Embed(
        title="Ticket Hỗ Trợ",
        description="Nếu bạn cần mua hàng hoặc hỗ trợ, hãy bấm vào các nút bên dưới.\n**VUI LÒNG KHÔNG SPAM TICKET**",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete(delay=5)

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def close(ctx):
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        await ctx.send("Đóng ticket...")
        await ctx.channel.delete()
    else:
        await ctx.send("Lệnh này chỉ dùng trong ticket.")

#-------------------------------------------------My Help-----------------------------------------------------------
@bot.command(name="myhelp")
@commands.has_role(DEV_ROLE_NAME)
async def help_command(ctx):
    # Xóa lệnh gọi !help sau 5 giây
    await ctx.message.delete(delay=5)
    
    embed = discord.Embed(
        title="📜 Các lệnh hiện có:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="ow!myhelp", value="Hiện danh sách các lệnh của bot OW Support (Admin)", inline=False)
    embed.add_field(name="ow!banggia", value="Gửi bảng giá vào kênh Bảng Giá (Admin)", inline=False)
    embed.add_field(name="ow!bg <tên dịch vụ>", value="Gửi các bản giá riêng lẻ trong ticket (Admin)", inline=False)
    embed.add_field(name="ow!giveaway <thời gian> <phần thưởng>", value="Tạo giveaway (Admin)", inline=False)
    embed.add_field(name="ow!list_giveaways", value="Xem danh sách giveaway (Admin)", inline=False)
    embed.add_field(name="ow!endgiveaway <message_id>", value="Kết thúc giveaway ngay lập tức (Admin)", inline=False)
    embed.add_field(name="ow!reroll <message_id>", value="Random lại người trúng thưởng (Admin)", inline=False)
    embed.add_field(name="ow!thanhtoan <số tiền> <nội dung>", value="Tạo mã QR theo nội dung, tiền (Admin)", inline=False)
    embed.add_field(name="ow!sendticket", value="Gửi ticket vào kênh (Admin)", inline=False)
    embed.add_field(name="ow!adduser @user", value="Thêm người vào ticket (Admin)", inline=False)
    embed.add_field(name="ow!removeuser @user", value="Xóa người ra khỏi ticket (Admin)", inline=False)
    embed.add_field(name="ow!clear <số lượng>", value="Xóa tin nhắn theo số lượng (Admin)", inline=False)
    embed.add_field(name="ow!clearallhard", value="Xóa sạch kênh (Admin)", inline=False)
    
    # Thêm ảnh vào embed (thay link ảnh thành của bạn)
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif")
    
    await ctx.send(embed=embed)

#------------------------------------------------------------------------------------------------------------

#---------------------------------------------THANH TOÁN---------------------------------------------------------------
@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def thanhtoan(ctx, *, args: str):
    await ctx.message.delete(delay=5)

    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        bank_code = "VCB"
        account_no = "1034298524"
        account_name = "MAI LIEM TRUC"

        # args có thể là "1000000 Nội dung" hoặc "Nội dung"
        parts = args.split(' ', 1)  # tách 1 lần, phần đầu có thể là số tiền

        if len(parts) == 0:
            return await ctx.send("❌ Vui lòng nhập nội dung hoặc số tiền và nội dung.")

        try:
            sotien = int(parts[0].replace(',', ''))  # cố gắng parse số tiền đầu tiên
            loi_nhan = parts[1] if len(parts) > 1 else ""
            has_amount = True
        except ValueError:
            sotien = None
            loi_nhan = args
            has_amount = False

        loi_nhan_encoded = loi_nhan.replace(" ", "+")
        account_name_encoded = account_name.replace(" ", "+")

        if has_amount:
            qr_url = (
                f"https://img.vietqr.io/image/{bank_code}-{account_no}-compact.png"
                f"?amount={sotien}&addInfo={loi_nhan_encoded}&accountName={account_name_encoded}"
            )
            note = f"Số Tiền:\n{sotien:,} VND\n\n"
        else:
            qr_url = (
                f"https://img.vietqr.io/image/{bank_code}-{account_no}-compact.png"
                f"?addInfo={loi_nhan_encoded}&accountName={account_name_encoded}"
            )
            note = "Khách hàng tự nhập số tiền khi chuyển.\n\n"

        info_block = (
            f"```ini\n"
            f"Ngân hàng:\nVietcombank\n\n"
            f"Số Tài Khoản:\n{account_no}\n\n"
            f"Chủ Tài Khoản:\n{account_name}\n\n"
            f"{note}"
            f"Nội dung chuyển:\n{loi_nhan}\n\n"
            f"Ghi chú:\nKhách hàng vui lòng gửi bill vào ticket.\n"
            f"```"
        )

        embed = discord.Embed(
            title="Thông Tin Thanh Toán",
            description=info_block,
            color=discord.Color.green()
        )
        embed.set_image(url=qr_url)
        embed.set_footer(text="Mọi thắc mắc liên hệ OW.")

        await ctx.send(embed=embed)

    else:
        await ctx.send("Lệnh này chỉ dùng trong kênh ticket.")
#------------------------------------------------------------------------------------------------------------

#-------------------------------------------------Thêm/Xóa User Ticket--------------------------------------------------------------------
@bot.command(name="adduser")
@commands.has_role(DEV_ROLE_NAME)
async def add_user_to_ticket(ctx, member: discord.Member):
    # Kiểm tra xem có phải đang trong kênh ticket không
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        # Cập nhật permission cho user mới
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
        await ctx.send(f"✅ Đã thêm {member.mention} vào ticket.")
    else:
        await ctx.send("❌ Lệnh này chỉ dùng trong kênh ticket.")

    await ctx.message.delete(delay=5)


@bot.command(name="removeuser")
@commands.has_role(DEV_ROLE_NAME)
async def remove_user_from_ticket(ctx, member: discord.Member):
    if ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]:
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"🚫 Đã xoá {member.mention} khỏi ticket.")
    else:
        await ctx.send("❌ Lệnh này chỉ dùng trong kênh ticket.")

    await ctx.message.delete(delay=5)
#---------------------------------------------------------------------------------------------------------------------

#-------------------------------------------------Clear Kênh--------------------------------------------------------------------
@bot.command(name="clearallhard")
@commands.has_role(DEV_ROLE_NAME)
async def clear_all_hard(ctx):
    channel = ctx.channel

    # Xóa lệnh gọi trước
    try:
        await ctx.message.delete()
    except:
        pass

    # Clone và xóa kênh
    new_channel = await channel.clone(reason="Clear all messages")
    await channel.delete()

    # Gửi thông báo và xóa nó sau 5 giây
    msg = await new_channel.send("✅ Tất cả tin nhắn trong kênh đã được xóa (kênh đã được tạo lại).")
    await asyncio.sleep(5)
    await msg.delete()


@bot.command(name="clear")
@commands.has_role(DEV_ROLE_NAME)
async def clear_messages(ctx, amount: int):
    # Xóa cả tin nhắn gọi lệnh => +1
    deleted = await ctx.channel.purge(limit=amount + 1)

    confirm_msg = await ctx.send(f"🧹 Đã xóa {len(deleted) - 1} tin nhắn.")
    await asyncio.sleep(5)
    await confirm_msg.delete()

    try:
        await ctx.message.delete(delay=5)
    except:
        pass

#---------------------------------------------------------------------------------------------------------------------

#--------------------------------------------BẢNG GIÁ----------------------------------------------------------------
# BẢNG GIÁ TỪNG DỊCH VỤ
product_data = {
    "Auto Fram": 
    (
    "**🚀 DỊCH VỤ AUTO FRAM – Nhanh, Mượt, Hiệu Quả**\n"
    "• Key │15k/ngày | 90k/tuần | 160k/tháng | 300k/vv\n"
    "• Key vĩnh viễn (full quyền tất cả tool OW STORE) │1tr2\n"
    "• Nhận viết Auto theo yêu cầu – cá nhân hóa 100%"
    ),

    "Cày thuê GTA5VN": 
    (
    "**🎮 CÀY THUÊ GTA5VN – Lên Level Không Cần Cày**\n"
    "• Cày theo yêu cầu riêng\n"
    "• SV2 từ LV0 ➜ LV25 │Chỉ 90k"
    ),

    "Thiết kế đồ họa": 
    (
    "**🎨 THIẾT KẾ ĐỒ HỌA – Đẹp Mắt, Đúng Chất Bạn**\n"
    "• Nhận vẽ Logo, Banner, Poster, Social Post theo yêu cầu"
    ),

    "Thiết kế Discord": 
    (
    "**🤖 DISCORD SETUP & CODE BOT TÙY CHỈNH**\n"
    "• Thiết kế server chuyên nghiệp │50k\n"
    "• Code bot theo yêu cầu (ticket, QR, thống kê...) │100k – 500k"
    ),

    "Word/Excel/PowerPoint/Canva": 
    (
    "**📄 VĂN PHÒNG – THIẾT KẾ TRÌNH CHIẾU – CANVA**\n"
    "• PowerPoint/Canva │8k/slide (giảm nếu nhiều)\n"
    "• Word & Excel: tùy nội dung & yêu cầu"
    ),

    "Cài phần mềm": 
    (
    "**🧩 CÀI PHẦN MỀM BẢN QUYỀN – SIÊU ƯU ĐÃI**\n"
    "• Adobe AI + Photoshop │150k trọn gói\n"
    "• Microsoft Office Full Bộ │150k cài trọn đời"
    ),

}


class BangGiaDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, description=f"Xem bảng giá {label}")
            for label in product_data.keys()
        ]
        super().__init__(
            placeholder="Chọn một dịch vụ...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        has_role = any(role.name == MEM_ROLE_NAME for role in member.roles)

        if not has_role:
            await interaction.response.send_message(
                "❌ Bạn cần có role MEM để sử dụng tính năng này.", ephemeral=True
            )
            return

        selected = self.values[0]
        content = product_data[selected]
        embed = discord.Embed(
            title=f"Bảng giá: {selected}",
            description=content,
            color=discord.Color.green()
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BangGiaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BangGiaDropdown())


@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def banggia(ctx):
    # Tìm kênh bảng giá theo tên
    channel = discord.utils.get(ctx.guild.channels, name="📰│bảng-giá")
    if channel is None:
        await ctx.send("Không tìm thấy kênh bảng giá 📰│bảng-giá!")
        return

    embed = discord.Embed(
        title="🛒 Menu OW STORE – Xem Là Mê, Mua Là Phê",
        description="Hãy chọn dịch vụ bạn quan tâm bên dưới để xem chi tiết.\nNhấn <#1351232807908675614> để được tư vấn nhanh chóng từ đội ngũ OW STORE.",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif")
    embed.set_footer(text="DEV BY OW")

    await channel.send(embed=embed, view=BangGiaView())  # Gửi embed vào kênh bảng giá
    await ctx.message.delete(delay=5)  # Xóa lệnh người dùng sau 5 giây


@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def bg(ctx, *, service: str = None):
    # Kiểm tra xem lệnh có được gọi trong kênh thuộc category ticket hay không
    if not (ctx.channel.category and ctx.channel.category.name in [CATEGORY_BUY, CATEGORY_SUPPORT]):
        await ctx.send("Lệnh này chỉ được sử dụng trong kênh ticket.")
        return

    if not service:
        await ctx.send("Vui lòng nhập tên dịch vụ cần xem bảng giá. Ví dụ: `!bg autofram`")
        return

    service_lower = service.lower()

    matched_key = None
    for key in product_data.keys():
        if service_lower in key.lower():
            matched_key = key
            break

    if matched_key:
        embed = discord.Embed(
            title=f"Bảng Giá: {matched_key}",
            description=product_data[matched_key],
            color=discord.Color.green()
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Không tìm thấy dịch vụ phù hợp với '{service}'. Vui lòng thử lại.")
    
    await ctx.message.delete(delay=5)
#------------------------------------------------------------------------------------------------------------

#--------------------------------------------------CHÀO MỪNG----------------------------------------------------------
@bot.event
async def on_member_join(member):
    # Tìm kênh chào mừng theo tên
    channel = discord.utils.get(member.guild.text_channels, name="🎉│chào-mừng")
    if channel is None:
        return

    # Thay ID bên dưới bằng ID thật của từng kênh
    update_channel_id = 1351223923966083152  # 🚨│update
    rule_channel_id = 1351226270414934091   # 📖│luật-dịch-vụ
    ticket_channel_id = 1351232807908675614 # 🎫│ticket
    price_channel_id = 1351224397427642490  # 📰│bảng-giá (ID giả, thay bằng ID thật)

    embed = discord.Embed(
        description=f"Chào mừng {member.mention} đã đến với **OW STORE**. Chúng tôi hy vọng bạn sẽ hài lòng khi đến với store của chúng tôi.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="\u200b",
        value=f"• Hãy xem kênh <#{update_channel_id}> để nhận thông báo mỗi khi chúng tôi có thay đổi hoặc sự kiện hấp dẫn.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là luật khi sử dụng dịch vụ tại store của chúng tôi <#{rule_channel_id}>.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là nơi để bạn mua hàng hoặc cần chúng tôi hỗ trợ bảo hành <#{ticket_channel_id}>.",
        inline=False
    )
    embed.add_field(
        name="\u200b",
        value=f"• Đây là bảng giá dịch vụ tại store của chúng tôi <#{price_channel_id}>.",
        inline=False
    )

    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1351234840749670430/1351423170443477023/logo2.png?ex=68222c28&is=6820daa8&hm=a2256de50600ffc0074e82e69fa2887477c9055c4b0f7e6c03fd0e4a179abb1b&=&format=webp&quality=lossless")
    embed.set_image(url="https://media.discordapp.net/attachments/1351234840749670430/1371308366030176377/ow.gif?ex=6822a9f0&is=68215870&hm=a521cfdb679132bbf79ebe91a08a52b149a81299fa1c396eb92882f679203eb9&=")  # đổi link ảnh tùy bạn

    await channel.send(embed=embed)
#------------------------------------------------------------------------------------------------------------


#-----------------------------------------------GIVEAWAY-------------------------------------------------------------
class GiveawayView(View):
    def __init__(self, giveaway_message, end_callback=None):
        super().__init__(timeout=None)
        self.participants = set()
        self.giveaway_message = giveaway_message
        self.end_callback = end_callback

    @discord.ui.button(label="Tham gia Giveaway", style=discord.ButtonStyle.green, custom_id="giveaway_join")
    async def join_button(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        if user.id in self.participants:
            await interaction.response.send_message("Bạn đã tham gia rồi!", ephemeral=True)
        else:
            self.participants.add(user.id)
            await interaction.response.send_message("Bạn đã tham gia giveaway!", ephemeral=True)
            await self.update_embed()

    async def update_embed(self):
        embed = self.giveaway_message.embeds[0]
        lines = embed.description.splitlines()

        # Loại bỏ dòng cũ nếu đã có
        lines = [line for line in lines if not line.startswith("Số người tham gia:")]

        # Thêm dòng mới hiển thị số người tham gia
        lines.insert(2, f"Số người tham gia: **{len(self.participants)}**")

        embed.description = "\n".join(lines)
        await self.giveaway_message.edit(embed=embed, view=self)

    async def end_giveaway(self):
        if self.participants:
            participants = list(self.participants)
            while participants:
                winner_id = random.choice(participants)
                winner = self.giveaway_message.guild.get_member(winner_id)
                if winner:
                    # Gửi tin nhắn chúc mừng
                    try:
                        prize = self.giveaway_message.embeds[0].description.splitlines()[0].split("**")[1]
                    except Exception:
                        prize = "phần thưởng"
                    try:
                        await winner.send(
                            f"🎉 Chúc mừng bạn đã thắng giveaway: **{prize}** 🎉"
                        )
                    except discord.Forbidden:
                        pass

                    await self.giveaway_message.channel.send(f"🎉 Giveaway kết thúc! Người thắng là {winner.mention} 🎉")
                    # Xóa giveaway khỏi bộ nhớ vì đã có người thắng hợp lệ
                    giveaway_views.pop(self.giveaway_message.id, None)
                    self.clear_items()
                    await self.giveaway_message.edit(view=None)
                    ended_giveaways[self.giveaway_message.id] = self
                    return
                else:
                    participants.remove(winner_id)

            # Không tìm được người thắng hợp lệ (tất cả người tham gia không còn trong server)
            await self.giveaway_message.channel.send(
                f"🎉 Giveaway kết thúc nhưng không thể xác định người thắng (không ai còn trong server).\n"
                f"👉 Bạn có thể dùng lệnh `ow!reroll {self.giveaway_message.id}` để quay lại từ danh sách ban đầu."
            )
            # **Giữ giveaway trong giveaway_views để reroll được**
            self.clear_items()
            await self.giveaway_message.edit(view=None)
            ended_giveaways[self.giveaway_message.id] = self
        else:
            # Không có người tham gia
            await self.giveaway_message.channel.send("Giveaway kết thúc nhưng không có người tham gia nào.")
            giveaway_views.pop(self.giveaway_message.id, None)
            self.clear_items()
            await self.giveaway_message.edit(view=None)
            ended_giveaways[self.giveaway_message.id] = self



def parse_time_string(time_str: str) -> int:
    time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    match = re.fullmatch(r"(\d+)([dhms])", time_str.lower())
    if not match:
        raise commands.BadArgument("Định dạng thời gian không hợp lệ. Dùng ví dụ: `1d`, `2h`, `30m`, `45s`")
    value, unit = match.groups()
    return int(value) * time_units[unit]

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def giveaway(ctx, time_str: str, *, prize: str):
    await ctx.message.delete(delay=5)

    try:
        time_in_seconds = parse_time_string(time_str)
    except commands.BadArgument as e:
        return await ctx.send(str(e))

    end_time = datetime.now(VN_TZ) + timedelta(seconds=time_in_seconds)
    end_timestamp = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 Giveaway Đã Bắt Đầu! 🎉",
        description=f"Phần thưởng: **{prize}**\n"
                    f"Kết thúc vào: <t:{end_timestamp}:F> (<t:{end_timestamp}:R>)\n"
                    "Số người tham gia: **0**\n\n"
                    "Nhấn nút bên dưới để tham gia giveaway!",
        color=discord.Color.gold()
    )

    giveaway_message = await ctx.send(embed=embed, view=None)
    view = GiveawayView(giveaway_message)
    giveaway_views[giveaway_message.id] = view
    await giveaway_message.edit(view=view)

    await asyncio.sleep(time_in_seconds)
    await view.end_giveaway()

@bot.command()
@commands.has_role(DEV_ROLE_NAME)
async def reroll(ctx, message_id: int):
    await ctx.message.delete(delay=5)
    view = giveaway_views.get(message_id)
    if not view:
        return await ctx.send("Không tìm thấy giveaway tương ứng hoặc đã kết thúc.")

    participants = list(view.participants)
    if not participants:
        return await ctx.send("Không có người tham gia trong giveaway này.")

    while participants:
        winner_id = random.choice(participants)
        winner = ctx.guild.get_member(winner_id)
        if winner:
            await ctx.send(f"Quay lại: Người thắng mới là {winner.mention} 🎉")
            try:
                await winner.send("Bạn đã được chọn lại là người thắng giveaway!")
            except discord.Forbidden:
                pass
            return
        else:
            participants.remove(winner_id)

    await ctx.send("Không thể tìm thấy người nào để chọn lại.")


@bot.command(name="list_giveaways")
@commands.has_role(DEV_ROLE_NAME)
async def list_giveaways(ctx):
    await ctx.message.delete(delay=5)
    active = []
    for view in giveaway_views.values():
        embed = view.giveaway_message.embeds[0]
        prize = embed.description.splitlines()[0].split("**")[1]
        end_line = [line for line in embed.description.splitlines() if "Kết thúc vào" in line][0]
        active.append(f"- `{view.giveaway_message.id}` | 🎁 {prize} | {end_line}")

    ended = []
    for msg_id, view in ended_giveaways.items():
        embed = view.giveaway_message.embeds[0]
        prize = embed.description.splitlines()[0].split("**")[1]
        ended.append(f"- `{msg_id}` | 🎁 {prize}")

    embed = discord.Embed(title="📋 Danh sách Giveaway", color=discord.Color.blurple())
    embed.add_field(name="🎯 Đang diễn ra", value="\n".join(active) or "Không có", inline=False)
    embed.add_field(name="✅ Đã kết thúc", value="\n".join(ended) or "Không có", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="endgiveaway")
@commands.has_role(DEV_ROLE_NAME)
async def end_giveaway_now(ctx, message_id: int):
    await ctx.message.delete(delay=5)
    view = giveaway_views.get(message_id)
    if not view:
        return await ctx.send("Không tìm thấy giveaway đang diễn ra với ID này.")

    await ctx.send(f"⏹️ Kết thúc giveaway `{message_id}` ngay lập tức.")
    await view.end_giveaway()
#------------------------------------------------------------------------------------------------------------


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Bạn không có quyền để dùng lệnh này.")

@bot.event
async def on_ready():
    # Thêm view tùy chỉnh
    bot.add_view(TicketView())

    # Cập nhật trạng thái bot
    activity = discord.Activity(type=discord.ActivityType.watching, name="OW STORE - Xem Là Mê, Mua Là Phê🔥")
    await bot.change_presence(activity=activity)

    print(f'Bot is ready: {bot.user}')




app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
