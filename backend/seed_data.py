import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME",   "college_club_compass")

CLUBS = [
    {
        "name": "TechnoByte",
        "domain": "Technical",
        "tagline": "Official CS Dept Technical Society",
        "description": "TechnoByte is the official technical society of the Computer Engineering Department at NIT Kurukshetra. It promotes coding culture, development skills, competitive programming, and peer-to-peer mentorship among students.",
        "members": 150,
        "founded": 2015,
        "email": "technobyte@nitkkr.ac.in",
        "tags": ["coding","web","DSA","hackathon","competitive programming"],
        "icon": "💻",
        "events": ["Hackshetra", "BlackBox", "Excalibur", "Web Hunt", "Techspardha Events"],
        "recruitment_info": "Open mainly for Computer Engineering students. Selection based on basic coding knowledge, development skills, and interview + task round.",
        "image_url": "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=800&auto=format&fit=crop"
    },
    {
        "name": "Innovation Cell (I-CELL)",
        "domain": "Management",
        "tagline": "Entrepreneurship & Innovation Hub",
        "description": "I-CELL is the entrepreneurship and innovation hub of NIT Kurukshetra. It promotes startup culture, business thinking, and innovation among students by providing mentorship, resources, and a platform to convert ideas into real ventures.",
        "members": 120,
        "founded": 2016,
        "email": "icell@nitkkr.ac.in",
        "tags": ["entrepreneurship","startup","innovation","business","E-Summit"],
        "icon": "🚀",
        "events": ["E-Summit", "Startup Pitch Competition", "Business Plan Competition", "Market IT", "Guest Lectures"],
        "recruitment_info": "Open to all branches. Selection based on entrepreneurial mindset, ideas, and motivation.",
        "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800&auto=format&fit=crop"
    },
    {
        "name": "Startup Cell",
        "domain": "Management",
        "tagline": "From Idea to Product to Business",
        "description": "Startup Cell at NIT Kurukshetra is dedicated to fostering a startup ecosystem on campus. It supports students who want to build their own ventures and understand the complete journey from idea to product to business.",
        "members": 90,
        "founded": 2017,
        "email": "startupcell@nitkkr.ac.in",
        "tags": ["startup","incubation","ideation","pitching","SIH"],
        "icon": "💡",
        "events": ["Ideation Bootcamps", "Smart India Hackathon", "Founder Talks", "Pitch Deck Sessions", "Networking Events"],
        "recruitment_info": "Open to all branches. Looking for motivated students with startup/product interest.",
        "image_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&auto=format&fit=crop"
    },
    {
        "name": "LSD — Let's Start Dance",
        "domain": "Cultural",
        "tagline": "Official Dance Club of NIT KKR",
        "description": "LSD is the official dance club of NIT Kurukshetra. It provides a platform for students passionate about dance to learn, perform, and represent the institute at cultural events and competitions. Covers hip-hop, contemporary, Bollywood, classical, B-boying and fusion styles.",
        "members": 80,
        "founded": 2010,
        "email": "lsd@nitkkr.ac.in",
        "tags": ["dance","hip-hop","Bollywood","classical","Confluence","performance"],
        "icon": "💃",
        "events": ["Confluence Performances", "Inter-college Competitions", "Flash Mobs", "Dance Showcases", "Workshops"],
        "recruitment_info": "Open to all branches. Selection via dance audition — rhythm, expressions, and stage confidence matter most. No professional experience required.",
        "image_url": "https://images.unsplash.com/photo-1547153760-18fc86324498?w=800&auto=format&fit=crop"
    },
    {
        "name": "Embedded Systems & Robotics Club",
        "domain": "Technical",
        "tagline": "Build Intelligent Machines",
        "description": "The Embedded Systems & Robotics Club (EMR) focuses on designing and developing intelligent hardware systems and robots by integrating embedded programming, electronics, sensors, IoT, and automation. Provides practical exposure to real-world applications.",
        "members": 95,
        "founded": 2014,
        "email": "emr@nitkkr.ac.in",
        "tags": ["robotics","embedded","Arduino","IoT","automation","hardware"],
        "icon": "🤖",
        "events": ["Robotics Workshops", "Line Follower Competition", "IoT Projects", "Techspardha Events", "Hackathons"],
        "recruitment_info": "Open to all branches (especially ECE, EE, ME, CSE). Interest in robotics and hardware, basic technical aptitude needed.",
        "image_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&auto=format&fit=crop"
    },
    {
        "name": "SPIC MACAY",
        "domain": "Cultural",
        "tagline": "Promoting Indian Classical Music & Culture",
        "description": "SPIC MACAY (Society for the Promotion of Indian Classical Music And Culture Amongst Youth) is the cultural society dedicated to promoting Indian classical music, dance, and traditional heritage among students through live performances, lecture demonstrations, and interactive sessions.",
        "members": 60,
        "founded": 2008,
        "email": "spicmacay@nitkkr.ac.in",
        "tags": ["classical music","culture","dance","yoga","heritage","Hindustani"],
        "icon": "🎵",
        "events": ["Classical Music Concerts", "Dance Performances", "Yoga Sessions", "Heritage Workshops", "Cultural Baithaks"],
        "recruitment_info": "Open to all branches. Join as volunteer or organizing member. Interest in Indian culture and dedication required.",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800&auto=format&fit=crop"
    },
    {
        "name": "Photography Club",
        "domain": "Cultural",
        "tagline": "The Creative Eye of NIT KKR",
        "description": "The Photography Club is the creative eye of NIT Kurukshetra. From capturing the biggest fest moments to candid hostel memories, the club tells the story of club life through photos and videos. Teaches camera handling, editing (Lightroom/Photoshop), and cinematography.",
        "members": 70,
        "founded": 2014,
        "email": "photog@nitkkr.ac.in",
        "tags": ["photography","videography","DSLR","editing","Confluence","aftermovie"],
        "icon": "📸",
        "events": ["Photowalks", "Photo Exhibitions", "Confluence Coverage", "Editing Workshops", "Short Films"],
        "recruitment_info": "Open to all. Mobile or DSLR — creativity matters most.",
        "image_url": "https://images.unsplash.com/photo-1452780212940-6f5c0d14d848?w=800&auto=format&fit=crop"
    },
    {
        "name": "MAD — Managing & Directing Club",
        "domain": "Management",
        "tagline": "We Run the Show, Behind the Scenes",
        "description": "MAD is the team that turns college events into grand experiences. While others perform on stage, MAD works behind the scenes to make everything happen perfectly. If you've ever wondered how Confluence runs so smoothly — the answer is MAD.",
        "members": 75,
        "founded": 2012,
        "email": "mad@nitkkr.ac.in",
        "tags": ["event management","Confluence","Techspardha","organizing","backstage"],
        "icon": "🎬",
        "events": ["Confluence Management", "Techspardha Coordination", "Stage Management", "Guest Events"],
        "recruitment_info": "Open to all. Looking for planners, leaders, and people who love being in action.",
        "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop"
    },
    {
        "name": "Aero Modelling Club",
        "domain": "Technical",
        "tagline": "Build. Fly. Compete.",
        "description": "The Aero Modelling Club focuses on designing RC planes, drones, and aerial robotics systems. Members build and test aircraft models and participate in national competitions and Techspardha events.",
        "members": 55,
        "founded": 2016,
        "email": "aeroclub@nitkkr.ac.in",
        "tags": ["drones","RC planes","aerospace","robotics","Techspardha"],
        "icon": "✈️",
        "events": ["Model Building Competitions", "Drone Racing", "Techspardha Events", "Workshops"],
        "recruitment_info": "Open to all branches. Passion for aviation and hands-on building preferred.",
        "image_url": "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=800&auto=format&fit=crop"
    },
    {
        "name": "MechSoc",
        "domain": "Technical",
        "tagline": "Engineering the Future in Metal",
        "description": "MechSoc is the Mechanical Engineering society that organizes design, manufacturing, robotics, and CAD-related technical events and workshops. Bridges the gap between theoretical knowledge and practical applications.",
        "members": 85,
        "founded": 2013,
        "email": "mechsoc@nitkkr.ac.in",
        "tags": ["mechanical","CAD","manufacturing","robotics","design","Techspardha"],
        "icon": "⚙️",
        "events": ["CAD Workshops", "Manufacturing Competitions", "Techspardha Events", "Design Challenges"],
        "recruitment_info": "Primarily for Mechanical and related branches. Interest in design and manufacturing.",
        "image_url": "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=800&auto=format&fit=crop"
    },
    {
        "name": "Anant — Math Society",
        "domain": "Literary",
        "tagline": "Where Numbers Tell Stories",
        "description": "Anant is the mathematical society of NIT KKR that promotes mathematics, logical thinking, and problem solving. Organizes math contests, seminars, coding competitions, and technical discussions.",
        "members": 65,
        "founded": 2015,
        "email": "anant@nitkkr.ac.in",
        "tags": ["mathematics","logic","problem-solving","competitive","seminars"],
        "icon": "📐",
        "events": ["Math Olympiads", "Problem Solving Contests", "Seminars", "Workshops"],
        "recruitment_info": "Open to all branches. Love for mathematics is all you need.",
        "image_url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800&auto=format&fit=crop"
    },
    {
        "name": "Fine Arts & Modelling Club",
        "domain": "Cultural",
        "tagline": "Creativity Without Limits",
        "description": "The Fine Arts & Modelling Club promotes art, stage creativity, modelling, and visual expression. Active during cultural events like Confluence, creating decorations, art installations, and stage designs.",
        "members": 50,
        "founded": 2011,
        "email": "finearts@nitkkr.ac.in",
        "tags": ["art","modelling","design","Confluence","visual arts","creativity"],
        "icon": "🎨",
        "events": ["Art Exhibitions", "Confluence Decoration", "Stage Design", "Sketch Competitions"],
        "recruitment_info": "Open to all. Any form of visual creativity welcomed.",
        "image_url": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800&auto=format&fit=crop"
    },
    {
        "name": "NSS",
        "domain": "Social",
        "tagline": "Not Me, But You",
        "description": "National Service Scheme unit of NIT KKR. Community service camps, health awareness drives, blood donation camps, and social impact initiatives throughout the year. Making a difference in the lives of those around us.",
        "members": 250,
        "founded": 2000,
        "email": "nss@nitkkr.ac.in",
        "tags": ["volunteering","community","social service","NSS","blood donation"],
        "icon": "🌍",
        "events": ["Community Service Camps", "Blood Donation Drives", "Health Awareness Programs", "Tree Plantation"],
        "recruitment_info": "Open to all. Community spirit and willingness to serve required.",
        "image_url": "https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=800&auto=format&fit=crop"
    },
    {
        "name": "Cricket Club",
        "domain": "Sports",
        "tagline": "Play Hard, Win Harder",
        "description": "NIT KKR's cricket team competing in inter-college and university tournaments. Regular practice sessions, fitness training, and participation in Techspardha sports events.",
        "members": 55,
        "founded": 2006,
        "email": "cricket@nitkkr.ac.in",
        "tags": ["cricket","sports","tournament","team","Techspardha"],
        "icon": "🏏",
        "events": ["Inter-College Tournaments", "Techspardha Cricket", "Practice Sessions", "Friendly Matches"],
        "recruitment_info": "Trials basis. All skill levels welcome for practice; competitive selection for tournaments.",
        "image_url": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=800&auto=format&fit=crop"
    },
    {
        "name": "DebateSoc",
        "domain": "Literary",
        "tagline": "Words That Change Minds",
        "description": "Parliamentary debate, Model UN, and public speaking. Participate in national debate competitions and sharpen your critical thinking and oratory skills.",
        "members": 70,
        "founded": 2011,
        "email": "debatesoc@nitkkr.ac.in",
        "tags": ["debate","MUN","public speaking","oratory","critical thinking"],
        "icon": "🗣️",
        "events": ["Techspardha Debate", "MUN", "Inter-College Competitions", "Workshops", "Open Debates"],
        "recruitment_info": "Open to all. Passion for discussion and current affairs welcome.",
        "image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800&auto=format&fit=crop"
    },
]

COLORS = {
    "Technical":"#6366f1","Cultural":"#ec4899",
    "Sports":"#f97316","Literary":"#14b8a6",
    "Social":"#22c55e","Management":"#f59e0b"
}

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    existing = await db.clubs.count_documents({})
    if existing >= 15:
        print(f"✅ Already have {existing} clubs. Skipping seed.")
        client.close()
        return

    await db.clubs.delete_many({})
    to_insert = [{"_id": str(ObjectId()), "color": COLORS.get(c["domain"],"#888"), **c} for c in CLUBS]
    await db.clubs.insert_many(to_insert)
    # Seed owner account
    owner_email = os.environ.get("OWNER_EMAIL", "")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not owner_email or not admin_pw:
        print("⚠️  OWNER_EMAIL or ADMIN_PASSWORD not set — skipping owner seed.")
        return
    
    owner = await db.users.find_one({"email": owner_email})
    if not owner:
        import bcrypt
        from datetime import datetime, timezone
        pw_hash = bcrypt.hashpw(admin_pw.encode(), bcrypt.gensalt()).decode()
        await db.users.insert_one({
            "_id": str(ObjectId()),
            "name": "Admin Raunak",
            "email": owner_email,
            "password": pw_hash,
            "role": "owner",
            "email_verified": True,
            "verified": True,
            "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
        })
        print(f"✅ Seeded owner account: {owner_email}")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
