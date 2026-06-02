import streamlit as st
from supabase import create_client, Client
import random

url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

def seed_looping():
    ptac_records = []
    counter = 1

    for floor in range(2, 7):
        for room in range(3, 30):
            if (room == 13 or room == 23):
                continue
            room_string = f"{floor}{room:02d}"
            if (room == 11):
                #PTAC A for suite
                ptac_records.append(
                    {
                        "ptac_id": f"PTAC-{counter:03d}",
                        "serial_number": f"AMN-{random.randint(100000, 999999)}",
                        "model_specs": "Amana PTAC12-Standard",
                        "current_location_name": f"Suite {room_string}-A",
                        "location_type": "Room",
                        "operational_status": "Active"
                    }
                )
                counter += 1

                #second PTAC for suite
                ptac_records.append(
                    {
                        "ptac_id": f"PTAC-{counter:03d}",
                        "serial_number": f"AMN-{random.randint(100000, 999999)}",
                        "model_specs": "Amana PTAC12-Standard",
                        "current_location_name": f"Suite {room_string}-B",
                        "location_type": "Room",
                        "operational_status": "Active"
                    }
                )
                counter += 1

            #regular rooms
            else:
                ptac_records.append(
                    {
                        "ptac_id": f"PTAC-{counter:03d}",
                        "serial_number": f"AMN-{random.randint(100000, 999999)}",
                        "model_specs": "Amana PTAC12-Standard",
                        "current_location_name": f"Room {room_string}",
                        "location_type": "Room",
                        "operational_status": "Active"
                    }
                )
                counter += 1

        #hallway PTACs        
        ptac_records.append(
            {
                "ptac_id": f"PTAC-{counter:03d}",
                "serial_number": f"AMN-{random.randint(100000, 999999)}",
                "model_specs": "Amana PTAC12-Standard",
                "current_location_name": f"Floor {floor} Corridor",
                "location_type": "Hallway",
                "operational_status": "Active"
            }
        )
        counter += 1
    
    #elevator closet
    ptac_records.append(
        {
            "ptac_id": f"PTAC-{counter:03d}",
            "serial_number": f"AMN-{random.randint(100000, 999999)}",
            "model_specs": "Amana PTAC12-Standard",
            "current_location_name": f"Elevator Closet",
            "location_type": "Elevator Closet",
            "operational_status": "Active"
        }
    )
    counter += 1
            
            
    st.title("Hotel Database")

    if st.button("Seed PTAC Data"):
        st.write("Seeding PTAC data...")
        supabase.table("ptac_units").delete().neq("ptac_id", "").execute()
        st.write("Pre-existing PTAC data cleared.")
        supabase.table("ptac_units").insert(ptac_records).execute()
        st.success("PTAC data seeded successfully!")


seed_looping()

