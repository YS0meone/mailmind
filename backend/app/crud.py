from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import User, DbUser
from app.logger_config import get_logger
from app.models import DbEmail, DbThread, Email
from sqlalchemy import select
from app.models import DbUser, Email, Thread
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

logger = get_logger(__name__)

async def upsert_user(*, session: AsyncSession, user: User) -> DbUser | None:
    # check if the user with given email exists
    stmt = select(DbUser).where(DbUser.email == user.email)
    result = await session.execute(stmt)
    db_user = result.scalar_one_or_none()
    if db_user:
        # if user exists, update the existing user
        db_user.accountId = user.accountId
        db_user.accountToken = user.accountToken
        db_user.lastDeltaToken = user.lastDeltaToken
        await session.commit()
        await session.refresh(db_user)
        logger.info(f"Updated existing user: {db_user}")
         # Return the updated user
        return db_user
    else:
        new_user = DbUser(
            accountId=user.accountId,
            accountToken=user.accountToken,
            email=user.email,
            lastDeltaToken=user.lastDeltaToken
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Inserted new user: {new_user}")
         # Return the newly created user
        return new_user

def convert_to_email(email: dict) -> Email:
    email_dict = email.copy()
    
    # Convert address fields
    email_dict['toAddrs'] = [addr["address"] for addr in email_dict.get('to', [])]
    if 'to' in email_dict:
        del email_dict['to']
        
    email_dict['ccAddrs'] = [addr["address"] for addr in email_dict.get('cc', [])]
    if 'cc' in email_dict:
        del email_dict['cc']
        
    email_dict['bccAddrs'] = [addr["address"] for addr in email_dict.get('bcc', [])]
    if 'bcc' in email_dict:
        del email_dict['bcc']
        
    email_dict['replyToAddrs'] = [addr["address"] for addr in email_dict.get('replyTo', [])]
    if 'replyTo' in email_dict:
        del email_dict['replyTo']
        
    email_dict['fromAddr'] = email_dict.get('from', {}).get('address', '')
    if 'from' in email_dict:
        del email_dict['from']
    
    # Set lastModifiedTime if not provided or None
    if not email_dict.get('lastModifiedTime'):
        email_dict['lastModifiedTime'] = email_dict.get('createdTime') or email_dict.get('sentAt')
    
    # Create Email object first
    ret = Email.model_validate(email_dict)
    
    # Then convert timezone-aware datetimes to naive after validation
    ret.createdTime = ret.createdTime.replace(tzinfo=None) if ret.createdTime.tzinfo else ret.createdTime
    ret.lastModifiedTime = ret.lastModifiedTime.replace(tzinfo=None) if ret.lastModifiedTime.tzinfo else ret.lastModifiedTime
    ret.sentAt = ret.sentAt.replace(tzinfo=None) if ret.sentAt.tzinfo else ret.sentAt
    ret.receivedAt = ret.receivedAt.replace(tzinfo=None) if ret.receivedAt.tzinfo else ret.receivedAt
    
    return ret

def generate_db_thread(record: dict, associated_email: Email) -> Thread:
    thread_dict = {}
    # Use the threadId from the record, not the email ID
    thread_dict['id'] = record.get('threadId')  # Changed from record.get('id')
    thread_dict['subject'] = record.get('subject')
    thread_dict['brief'] = associated_email.bodySnippet

    # Convert to naive datetime
    received_at = record.get('receivedAt')
    if isinstance(received_at, str):
        dt = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
        thread_dict['lastMessageDate'] = dt.replace(tzinfo=None)
    else:
        thread_dict['lastMessageDate'] = received_at.replace(tzinfo=None) if received_at.tzinfo else received_at
    
    thread_dict['involvedEmails'] = [record["from"]['address']]
    involved_attrs = ['to', 'cc', 'bcc', 'replyTo']
    for attr in involved_attrs:
        if attr in record:
            for addr in record[attr]:
                thread_dict['involvedEmails'].append(addr['address'])
    return Thread.model_validate(thread_dict)
    

def process_records(records: list[dict]) -> tuple[list[Email], list[Thread]]:
    emails = []
    thread_dict = {}  # Group by threadId to avoid duplicates
    
    for record in records:
        # Process email
        email = convert_to_email(record)
        emails.append(email)
        
        # Process thread - only create one thread per threadId
        thread_id = record.get('threadId')
        if thread_id not in thread_dict:
            thread = generate_db_thread(record, email)
            thread_dict[thread_id] = thread
        else:
            # Update existing thread with additional involved emails
            existing_thread = thread_dict[thread_id]
            new_emails = [record["from"]['address']]
            for attr in ['to', 'cc', 'bcc', 'replyTo']:
                if attr in record:
                    for addr in record[attr]:
                        new_emails.append(addr['address'])
            
            # Merge with existing involved emails and deduplicate
            all_emails = set(existing_thread.involvedEmails + new_emails)
            existing_thread.involvedEmails = list(all_emails)
            
            # Update with latest message date if newer
            received_at = record.get('receivedAt')
            if isinstance(received_at, str):
                dt = datetime.fromisoformat(received_at.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                dt = received_at.replace(tzinfo=None) if received_at.tzinfo else received_at
            
            if dt > existing_thread.lastMessageDate:
                existing_thread.lastMessageDate = dt
                existing_thread.subject = record.get('subject')  # Update subject to latest
    
    threads = list(thread_dict.values())
    return emails, threads

async def upsert_threads(session: AsyncSession, threads: list[Thread]) -> None:
    stmt = insert(DbThread).values([thread.model_dump() for thread in threads])
    update_values = { key: stmt.excluded[key] for key in DbThread.__table__.columns.keys() if key != 'id' }
    stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_=update_values    )
    await session.execute(stmt)
    await session.commit()
        

async def upsert_emails(session: AsyncSession, emails: list[Email]) -> None:
    stmt = insert(DbEmail).values([email.model_dump() for email in emails])
    update_values = { key: stmt.excluded[key] for key in DbEmail.__table__.columns.keys() if key != 'id' and key != 'threadId' }
    stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_=update_values    )
    await session.execute(stmt)
    await session.commit()

async def sync_emails_and_threads(session: AsyncSession, records: list[dict]) -> None:
    emails, threads = process_records(records)
    
    if threads:
        await upsert_threads(session, threads)
    else:
        logger.info("No threads to upsert.")

    if emails:
        await upsert_emails(session, emails)
    else:
        logger.info("No emails to upsert.")
    
    logger.info(f"Upserted {len(emails)} emails and {len(threads)} threads.")

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    -G https://api.aurinko.io/v1/email/sync/updated \
    -d deltaToken='H4sIAAAAAAAA_2NgZmBkAAPGt60MgiBGhvF0VwDJixd4FwAAAA'
'''

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    https://api.aurinko.io/v1/email/messages/19778fdd6eb3eaf9/raw
'''

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    https://api.aurinko.io/v1/email/messages/19778fdd6eb3eaf9
    '''