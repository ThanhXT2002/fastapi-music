# Hướng dẫn triển khai Frontend với Angular cho FastAPI Music API V3

## Tổng quan

FastAPI Music API V3 cung cấp một quy trình toàn diện để tải nhạc từ YouTube với các tính năng sau:

1. Phản hồi metadata ngay lập tức
2. Tải nhạc ngầm (background)
3. Kiểm tra trạng thái xử lý 
4. Tải xuống theo chunks
5. Hiển thị thumbnail

Tài liệu này mô tả cách triển khai một ứng dụng Angular để tương tác với API này.

## Luồng hoạt động

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Nhập URL   │────>│ Lấy thông   │────>│  Kiểm tra   │────>│  Tải file   │
│  YouTube    │     │ tin bài hát │     │  trạng thái │     │  nhạc       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Các API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/v3/songs/info` | POST | Lấy thông tin bài hát và bắt đầu tải |
| `/api/v3/songs/status/{song_id}` | GET | Kiểm tra trạng thái xử lý |
| `/api/v3/songs/download/{song_id}` | GET | Tải file nhạc |
| `/api/v3/songs/thumbnail/{song_id}` | GET | Lấy thumbnail |

## Triển khai Angular

### 1. Thiết lập dự án

```bash
ng new music-app --routing
cd music-app
ng generate service services/music
```

### 2. Model và Interface

Tạo các model và interface cho ứng dụng:

```typescript
// src/app/models/song.model.ts
export interface SongInfo {
  id: string;
  title: string;
  artist: string;
  thumbnail_url: string;
  duration: number;
  duration_formatted: string;
  keywords: string[];
  original_url: string;
  created_at: string;
}

export interface SongStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  audio_filename?: string;
  thumbnail_filename?: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}
```

### 3. Service

Triển khai Music Service để tương tác với API:

```typescript
// src/app/services/music.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { map, switchMap, takeWhile, tap } from 'rxjs/operators';
import { ApiResponse, SongInfo, SongStatus } from '../models/song.model';

@Injectable({
  providedIn: 'root'
})
export class MusicService {
  private apiUrl = 'http://localhost:8000/api/v3';
  private currentSongSubject = new BehaviorSubject<SongInfo | null>(null);
  private statusPollingSubject = new BehaviorSubject<SongStatus | null>(null);
  
  currentSong$ = this.currentSongSubject.asObservable();
  songStatus$ = this.statusPollingSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Lấy thông tin bài hát từ YouTube URL và bắt đầu tải về
   */
  getSongInfo(youtubeUrl: string): Observable<SongInfo> {
    return this.http.post<ApiResponse<SongInfo>>(`${this.apiUrl}/songs/info`, { youtube_url: youtubeUrl })
      .pipe(
        map(response => {
          if (!response.success) {
            throw new Error(response.message);
          }
          
          // Cập nhật current song
          this.currentSongSubject.next(response.data);
          
          // Bắt đầu polling trạng thái
          this.startStatusPolling(response.data.id);
          
          return response.data;
        })
      );
  }

  /**
   * Kiểm tra trạng thái xử lý của bài hát theo định kỳ
   */
  startStatusPolling(songId: string, pollInterval = 2000): void {
    interval(pollInterval)
      .pipe(
        switchMap(() => this.getSongStatus(songId)),
        takeWhile(status => status.status !== 'completed' && status.status !== 'failed', true)
      ).subscribe(status => {
        this.statusPollingSubject.next(status);
      });
  }

  /**
   * Lấy trạng thái xử lý của bài hát
   */
  getSongStatus(songId: string): Observable<SongStatus> {
    return this.http.get<ApiResponse<SongStatus>>(`${this.apiUrl}/songs/status/${songId}`)
      .pipe(
        map(response => {
          if (!response.success) {
            throw new Error(response.message);
          }
          return response.data;
        })
      );
  }

  /**
   * Lấy URL download cho bài hát
   */
  getDownloadUrl(songId: string): string {
    return `${this.apiUrl}/songs/download/${songId}`;
  }
  
  /**
   * Lấy URL thumbnail cho bài hát
   */
  getThumbnailUrl(songId: string): string {
    return `${this.apiUrl}/songs/thumbnail/${songId}`;
  }
  
  /**
   * Download và lưu file nhạc vào IndexedDB
   */
  downloadAndStoreAudio(songId: string): Observable<Blob> {
    return this.http.get(this.getDownloadUrl(songId), { responseType: 'blob' })
      .pipe(
        tap(audioBlob => {
          // Lưu vào IndexedDB cho sử dụng offline
          this.storeInIndexedDB(songId, audioBlob);
        })
      );
  }
  
  /**
   * Lưu file audio vào IndexedDB
   */
  private storeInIndexedDB(songId: string, audioBlob: Blob): void {
    const request = indexedDB.open('musicDB', 1);
    
    request.onupgradeneeded = (event: any) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('songs')) {
        db.createObjectStore('songs', { keyPath: 'id' });
      }
    };
    
    request.onsuccess = (event: any) => {
      const db = event.target.result;
      const transaction = db.transaction(['songs'], 'readwrite');
      const store = transaction.objectStore('songs');
      
      // Lưu song vào IndexedDB
      store.put({ 
        id: songId, 
        audioBlob: audioBlob, 
        timestamp: new Date().toISOString() 
      });
    };
  }
}
```

### 4. Component

#### a. Trang tìm kiếm và tải nhạc:

```typescript
// src/app/components/song-search/song-search.component.ts
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MusicService } from '../../services/music.service';
import { SongInfo, SongStatus } from '../../models/song.model';
import { Observable } from 'rxjs';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-song-search',
  templateUrl: './song-search.component.html',
  styleUrls: ['./song-search.component.scss']
})
export class SongSearchComponent {
  searchForm: FormGroup;
  loading = false;
  error = '';
  currentSong$: Observable<SongInfo | null>;
  songStatus$: Observable<SongStatus | null>;
  
  constructor(
    private fb: FormBuilder,
    private musicService: MusicService,
    private sanitizer: DomSanitizer
  ) {
    this.searchForm = this.fb.group({
      youtubeUrl: ['', [Validators.required, Validators.pattern('(https?://)?(www\\.)?(youtube\\.com|youtu\\.?be)/.+')]]
    });
    
    this.currentSong$ = this.musicService.currentSong$;
    this.songStatus$ = this.musicService.songStatus$;
  }
  
  onSubmit() {
    if (this.searchForm.invalid) {
      return;
    }
    
    this.loading = true;
    this.error = '';
    
    const youtubeUrl = this.searchForm.get('youtubeUrl')!.value;
    
    this.musicService.getSongInfo(youtubeUrl)
      .subscribe({
        next: () => {
          this.loading = false;
        },
        error: (err) => {
          this.error = err.message || 'Failed to get song info';
          this.loading = false;
        }
      });
  }
  
  getThumbnailUrl(songId: string): string {
    return this.musicService.getThumbnailUrl(songId);
  }
  
  getDownloadUrl(songId: string): string {
    return this.musicService.getDownloadUrl(songId);
  }
  
  downloadSong(songId: string): void {
    this.musicService.downloadAndStoreAudio(songId)
      .subscribe({
        next: (blob) => {
          // Tạo URL tạm thời để download
          const url = window.URL.createObjectURL(blob);
          
          // Tạo phần tử a ẩn để download
          const a = document.createElement('a');
          a.href = url;
          a.download = `song-${songId}.m4a`;
          document.body.appendChild(a);
          a.click();
          
          // Dọn dẹp
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        },
        error: (err) => {
          this.error = 'Failed to download song';
          console.error(err);
        }
      });
  }
  
  getSafeAudioUrl(songId: string): SafeUrl {
    const url = this.musicService.getDownloadUrl(songId);
    return this.sanitizer.bypassSecurityTrustUrl(url);
  }
  
  getProgressPercent(progress: number): string {
    return `${Math.round(progress * 100)}%`;
  }
}
```

```html
<!-- src/app/components/song-search/song-search.component.html -->
<div class="song-search-container">
  <h1>FastAPI Music Search</h1>
  
  <form [formGroup]="searchForm" (ngSubmit)="onSubmit()" class="search-form">
    <div class="form-group">
      <input 
        type="text" 
        formControlName="youtubeUrl" 
        placeholder="Enter YouTube URL"
        class="form-control"
      >
      <div class="error" *ngIf="searchForm.get('youtubeUrl')?.invalid && searchForm.get('youtubeUrl')?.touched">
        Please enter a valid YouTube URL
      </div>
    </div>
    
    <button 
      type="submit" 
      [disabled]="searchForm.invalid || loading"
      class="btn btn-primary"
    >
      <span *ngIf="loading">Loading...</span>
      <span *ngIf="!loading">Get Song</span>
    </button>
  </form>
  
  <div class="error-message" *ngIf="error">{{ error }}</div>
  
  <!-- Song Info -->
  <div class="song-info" *ngIf="currentSong$ | async as song">
    <div class="song-card">
      <div class="thumbnail">
        <img [src]="getThumbnailUrl(song.id)" [alt]="song.title">
      </div>
      
      <div class="details">
        <h2>{{ song.title }}</h2>
        <p class="artist">{{ song.artist }}</p>
        <p class="duration">Length: {{ song.duration_formatted }}</p>
        
        <!-- Song Status -->
        <div class="status" *ngIf="songStatus$ | async as status">
          <div class="status-label">
            Status: <span [ngClass]="status.status">{{ status.status }}</span>
          </div>
          
          <div class="progress-bar" *ngIf="status.status === 'processing' || status.status === 'pending'">
            <div class="progress" [style.width]="getProgressPercent(status.progress)"></div>
          </div>
          
          <div class="error-message" *ngIf="status.status === 'failed' && status.error_message">
            {{ status.error_message }}
          </div>
          
          <div class="actions" *ngIf="status.status === 'completed'">
            <!-- Player -->
            <audio controls [src]="getSafeAudioUrl(song.id)"></audio>
            
            <!-- Download Button -->
            <button class="btn btn-download" (click)="downloadSong(song.id)">
              Download
            </button>
            
            <!-- Direct Link -->
            <a [href]="getDownloadUrl(song.id)" download class="btn btn-link">
              Direct Download Link
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 5. HTTP Interceptor (Optional)

Nếu cần xử lý lỗi hoặc thêm headers:

```typescript
// src/app/interceptors/api.interceptor.ts
import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {

  constructor() {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Thêm headers nếu cần
    const apiRequest = request.clone({
      setHeaders: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    return next.handle(apiRequest).pipe(
      catchError((error: HttpErrorResponse) => {
        // Xử lý lỗi
        let errorMsg = '';
        if (error.error instanceof ErrorEvent) {
          // Client-side error
          errorMsg = `Error: ${error.error.message}`;
        } else {
          // Server-side error
          if (error.error && error.error.message) {
            errorMsg = error.error.message;
          } else {
            errorMsg = `Error Code: ${error.status}, Message: ${error.message}`;
          }
        }
        return throwError(() => new Error(errorMsg));
      })
    );
  }
}
```

Đăng ký interceptor trong AppModule:

```typescript
// src/app/app.module.ts
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SongSearchComponent } from './components/song-search/song-search.component';
import { ApiInterceptor } from './interceptors/api.interceptor';

@NgModule({
  declarations: [
    AppComponent,
    SongSearchComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ReactiveFormsModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: ApiInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

### 6. Lưu trữ offline với IndexedDB

```typescript
// src/app/services/indexed-db.service.ts
import { Injectable } from '@angular/core';
import { Observable, from, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class IndexedDBService {
  private dbName = 'musicDB';
  private dbVersion = 1;
  
  constructor() {
    this.initDB();
  }
  
  private initDB(): Observable<IDBDatabase> {
    return from(new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = () => reject(request.error);
      
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        if (!db.objectStoreNames.contains('songs')) {
          db.createObjectStore('songs', { keyPath: 'id' });
        }
        
        if (!db.objectStoreNames.contains('thumbnails')) {
          db.createObjectStore('thumbnails', { keyPath: 'id' });
        }
      };
    })).pipe(
      catchError(error => {
        console.error('Error initializing IndexedDB', error);
        throw error;
      })
    );
  }
  
  // Lưu file audio
  saveAudio(songId: string, audioBlob: Blob): Observable<string> {
    return this.initDB().pipe(
      map(db => {
        return new Observable<string>(observer => {
          const transaction = db.transaction(['songs'], 'readwrite');
          const store = transaction.objectStore('songs');
          
          const request = store.put({ 
            id: songId, 
            audioBlob: audioBlob,
            timestamp: new Date().toISOString()
          });
          
          request.onsuccess = () => {
            observer.next(songId);
            observer.complete();
          };
          
          request.onerror = () => {
            observer.error(request.error);
          };
        });
      }),
      catchError(error => {
        console.error('Error saving audio to IndexedDB', error);
        throw error;
      })
    );
  }
  
  // Lấy file audio
  getAudio(songId: string): Observable<Blob | null> {
    return this.initDB().pipe(
      map(db => {
        return new Observable<Blob | null>(observer => {
          const transaction = db.transaction(['songs'], 'readonly');
          const store = transaction.objectStore('songs');
          
          const request = store.get(songId);
          
          request.onsuccess = () => {
            if (request.result) {
              observer.next(request.result.audioBlob);
            } else {
              observer.next(null);
            }
            observer.complete();
          };
          
          request.onerror = () => {
            observer.error(request.error);
          };
        });
      }),
      catchError(error => {
        console.error('Error getting audio from IndexedDB', error);
        return of(null);
      })
    );
  }
}
```

### 7. Xử lý offline

Tạo các guard cho việc kiểm tra tình trạng offline:

```typescript
// src/app/guards/offline.guard.ts
import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class OfflineGuard implements CanActivate {
  
  constructor(private router: Router) {}
  
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean> {
      
    // Kiểm tra kết nối mạng
    if (navigator.onLine) {
      return of(true);
    } else {
      // Nếu đang offline, chuyển hướng đến trang offline
      this.router.navigate(['/offline']);
      return of(false);
    }
  }
}
```

### 8. Xử lý Chunked Downloads

Để hiển thị tiến trình download:

```typescript
// src/app/services/music.service.ts (thêm phương thức)
downloadWithProgress(songId: string): Observable<{progress: number, blob?: Blob}> {
  return new Observable(observer => {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', this.getDownloadUrl(songId), true);
    xhr.responseType = 'blob';
    
    // Xử lý tiến trình
    xhr.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = event.loaded / event.total;
        observer.next({progress: percentComplete});
      }
    };
    
    // Xử lý khi hoàn thành
    xhr.onload = () => {
      if (xhr.status === 200) {
        observer.next({progress: 1, blob: xhr.response});
        observer.complete();
      } else {
        observer.error(new Error(`HTTP error: ${xhr.status}`));
      }
    };
    
    // Xử lý lỗi
    xhr.onerror = () => {
      observer.error(new Error('Network error occurred'));
    };
    
    xhr.send();
    
    // Cleanup
    return () => {
      xhr.abort();
    };
  });
}
```

## Cải thiện UX

### 1. Toast Notifications

Sử dụng ngx-toastr hoặc xây dựng service thông báo:

```bash
ng add ngx-toastr
```

### 2. Theming

Tùy chỉnh giao diện mặc định của Angular Material hoặc Bootstrap:

```scss
/* styles.scss */
@import '~bootstrap/scss/bootstrap';

:root {
  --primary-color: #1db954;
  --secondary-color: #212529;
  --background-color: #f8f9fa;
  --text-color: #212529;
  --error-color: #dc3545;
  --success-color: #28a745;
}

/* Custom theme */
.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.song-card {
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow: hidden;
}
```

## Xử lý các trường hợp đặc biệt

### 1. Mất kết nối Internet

```typescript
// Trong component
@HostListener('window:offline')
onOffline() {
  this.isOffline = true;
  this.toastr.warning('You are offline. Some features may not work.', 'Warning');
}

@HostListener('window:online')
onOnline() {
  this.isOffline = false;
  this.toastr.success('You are back online!', 'Connected');
}
```

### 2. Tiếp tục download sau khi mất kết nối

```typescript
downloadWithResume(songId: string): Observable<Blob> {
  // Kiểm tra xem đã có phần nào của file trong IndexedDB chưa
  return this.indexedDBService.getPartialDownload(songId).pipe(
    switchMap(partialData => {
      if (partialData) {
        // Nếu đã có, sử dụng Range headers để tiếp tục download
        return this.downloadRange(songId, partialData.downloadedSize);
      } else {
        // Nếu chưa có, bắt đầu download mới
        return this.downloadWithProgress(songId);
      }
    })
  );
}
```

## Tối ưu hóa

### 1. Lazy Loading Modules

```typescript
// app-routing.module.ts
const routes: Routes = [
  { 
    path: 'songs',
    loadChildren: () => import('./modules/songs/songs.module').then(m => m.SongsModule)
  }
];
```

### 2. PWA Support

```bash
ng add @angular/pwa
```

## Tương thích trình duyệt

Ứng dụng tương thích với:
- Chrome (bản 70+)
- Firefox (bản 65+)
- Edge (bản 79+)
- Safari (bản 13+)

## Phát triển

### 1. Cài đặt dependencies

```bash
npm install
```

### 2. Start development server

```bash
ng serve
```

### 3. Build

```bash
ng build --prod
```

## Kết luận

Tài liệu này cung cấp các hướng dẫn toàn diện để triển khai ứng dụng Angular hoạt động với FastAPI Music API V3. Cách tiếp cận này đảm bảo:

1. **Giao diện người dùng responsive**: Trải nghiệm tốt trên cả desktop và mobile
2. **Streaming và caching**: Tối ưu cho audio lớn
3. **Hỗ trợ offline**: Người dùng có thể nghe nhạc đã tải
4. **UI/UX nhất quán**: Status và loading indicators
5. **Mở rộng dễ dàng**: Kiến trúc module hóa 

---

## Phụ lục: Xử lý đặc thù

### A. CORS

Đảm bảo FastAPI đã bật CORS:

```python
# Backend cần cấu hình để chấp nhận requests từ Angular
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### B. Authentication (nếu cần)

```typescript
// interceptor cần được mở rộng để thêm token vào header
const apiRequest = request.clone({
  setHeaders: {
    Authorization: `Bearer ${this.authService.getToken()}`
  }
});
```
