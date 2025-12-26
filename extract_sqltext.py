import os
import sys
import argparse
import oracledb # cx_Oracle 대체
from pathlib import Path

# 한글 주석 사용: Oracle DB에서 SQL 텍스트를 추출하여 파일로 저장하는 스크립트
# Python 3.13+ 호환을 위해 oracledb 라이브러리 사용 및 11g 접속을 위한 Thick Mode 적용

def extract_sql_text(user, password, host, port, sid, service_name, output_dir, client_dir=None, use_thick_mode=False):
    """
    Oracle DB에 접속하여 dp_sql_data 테이블에서 SQL을 추출합니다.
    기본값: Thin Mode (Clientless)
    옵션: Thick Mode (Oracle Client 사용, 11g 등 구버전 접속용)
    """
    
    # 1. Thick Mode 초기화 (사용자가 요청한 경우에만)
    if client_dir or use_thick_mode:
        try:
            if client_dir:
                print(f"[*] Oracle Client 경로 지정: {client_dir} (Thick Mode)")
                oracledb.init_oracle_client(lib_dir=client_dir)
            else:
                print(f"[*] 시스템 기본 Oracle Client 사용 (Thick Mode)")
                oracledb.init_oracle_client()
        except Exception as e:
            print("[!] Thick Mode 초기화 실패:")
            print(f"    {e}")
            if not client_dir:
                print("[!] 시스템 PATH에 Oracle Client가 없거나 아키텍처(32/64bit)가 맞지 않을 수 있습니다.")
                print("[!] --client-dir 옵션으로 경로를 명시하는 것을 권장합니다.")
            return
    else:
        print("[*] Thin Mode로 접속 시도 (Oracle Client 미사용)")
        print("    (Oracle 11g 등 구버전 DB는 접속 실패할 수 있습니다. 실패 시 --thick-mode 또는 --client-dir 사용 권장)")

    # DSN 생성
    if sid:
        dsn = oracledb.makedsn(host, port, sid=sid)
    elif service_name:
        dsn = oracledb.makedsn(host, port, service_name=service_name)
    else:
        print("[!] 오류: SID 또는 Service Name 중 하나는 필수입니다.")
        return

    print(f"[*] 연결 시도: {user}@{host}:{port} (DSN: {dsn})")
    
    try:
        # Oracle DB 접속
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        print("[*] DB 접속 성공")
        
        cursor = connection.cursor()
        
        # SQL 추출 쿼리 실행
        query = "SELECT job_type, id, sql_text FROM dp_sql_data"
        cursor.execute(query)
        
        count = 0
        
        # 결과 처리
        for job_type, sql_id, sql_clob in cursor:
            if not job_type or not sql_id:
                # print(f"[!] 경고: job_type 또는 id가 없는 데이터가 있습니다. (Skip)")
                continue
                
            # CLOB 데이터 읽기
            if sql_clob is None:
                sql_content = ""
            else:
                try:
                    # oracledb에서 CLOB는 read()로 읽거나 str()로 변환
                    sql_content = sql_clob.read() if hasattr(sql_clob, 'read') else str(sql_clob)
                except Exception as e:
                    print(f"[!] CLOB 읽기 오류 (ID: {sql_id}): {e}")
                    sql_content = ""

            # 저장 경로 생성
            clean_job_type = job_type.strip()
            clean_sql_id = sql_id.strip()
            
            target_dir = os.path.join(output_dir, clean_job_type)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            file_path = os.path.join(target_dir, f"{clean_sql_id}.sql")
            
            # 파일 쓰기
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(sql_content)
                count += 1
                if count % 100 == 0:
                    print(f"[*] {count}개 파일 추출 완료...")
            except IOError as e:
                print(f"[!] 파일 쓰기 오류 ({file_path}): {e}")

        print(f"[*] 총 {count}개의 SQL 파일이 추출되었습니다.")
        print(f"[*] 저장 위치: {output_dir}")

    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"[!] Oracle DB 오류: {error.code} - {error.message}")
        if "DP-1047" in str(e) or "ORA-12514" in str(e) or "ORA-12505" in str(e):
             pass
        elif not (client_dir or use_thick_mode): 
             print("\n[TIP] 접속 오류가 발생했습니다. Oracle 11g를 사용 중이라면 Thin Mode가 호환되지 않을 수 있습니다.")
             print("      이 경우, Oracle Instant Client를 설치하고 다음 옵션을 사용해 보세요:")
             print("      --client-dir [Client경로]  또는  --thick-mode")

    except Exception as e:
        print(f"[!] 오류 발생: {e}")
    finally:
        # 리소스 정리
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            print("[*] DB 연결 종료")

if __name__ == "__main__":
    import sys
    
    # 인자가 없이 실행된 경우 대화형 모드로 전환
    if len(sys.argv) == 1:
        print("[-] 명령행 인자가 입력되지 않아 대화형 모드로 실행합니다.")
        try:
            import getpass
            
            ip = input("DB IP: ").strip()
            port = input("DB Port (Enter for 1521): ").strip() or "1521"
            user = input("DB ID: ").strip()
            password = getpass.getpass("DB Password: ").strip()
            
            sid_or_service = input("접속 유형 (1: SID, 2: Service Name) [Default: 1]: ").strip()
            
            sid = None
            service_name = None
            
            if sid_or_service == '2':
                service_name = input("Service Name: ").strip()
            else:
                sid = input("SID: ").strip()

            print("\n[접속 모드 선택]")
            print("1. Thin Mode (기본값, Client 불필요, 12c+ 권장)")
            print("2. Thick Mode (Client 필요, 11g 호환용)")
            mode_sel = input("선택 [Enter for 1]: ").strip()
            
            client_dir = None
            use_thick_mode = False
            
            if mode_sel == '2':
                use_thick_mode = True
                client_dir = input("Oracle Client 경로 (비워두면 시스템 PATH 사용): ").strip() or None
                
            output_dir = input("저장 경로 (Enter for projects/sampleSrc/sqltext_extracted): ").strip() or "projects/sampleSrc/sqltext_extracted"
            
            # 필수 값 체크
            if not ip or not user or not password or (not sid and not service_name):
                print("[!] 필수 정보(IP, ID, Password, SID/Service Name)가 누락되었습니다.")
                sys.exit(1)

            # 출력 디렉토리 절대 경로 변환
            abs_output_dir = os.path.abspath(output_dir)
            
            extract_sql_text(user, password, ip, port, sid, service_name, abs_output_dir, client_dir, use_thick_mode)
            
        except KeyboardInterrupt:
            print("\n[!] 실행이 취소되었습니다.")
            sys.exit(0)
    else:
        parser = argparse.ArgumentParser(description="Oracle DB에서 SQL 텍스트를 추출하여 파일로 저장합니다.")
        
        # 필수 인자: 접속 정보
        parser.add_argument("--ip", required=True, help="DB 서버 IP")
        parser.add_argument("--port", default="1521", help="DB 포트 (기본값: 1521)")
        parser.add_argument("--id", required=True, dest="user", help="DB 사용자 ID")
        parser.add_argument("--password", required=True, help="DB 비밀번호")
        
        # 선택 인자 (SID 또는 Service Name 중 하나는 필수 처리 필요)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--sid", help="DB SID")
        group.add_argument("--service-name", help="DB Service Name")
        
        parser.add_argument("--client-dir", help="Oracle Instant Client 경로 (Thick Mode 사용 시)")
        parser.add_argument("--thick-mode", action="store_true", help="Oracle Client를 사용하는 Thick Mode 강제 사용 (시스템 PATH)")
        parser.add_argument("--output-dir", default="projects/sampleSrc/sqltext_extracted", help="결과물 저장 폴더 경로")
        
        args = parser.parse_args()
        
        # 출력 디렉토리 절대 경로 변환
        abs_output_dir = os.path.abspath(args.output_dir)
        
        extract_sql_text(args.user, args.password, args.ip, args.port, args.sid, args.service_name, abs_output_dir, args.client_dir, args.thick_mode)
