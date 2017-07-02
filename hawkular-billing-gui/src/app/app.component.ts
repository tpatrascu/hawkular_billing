import { Component } from '@angular/core';

import { Tenant } from './types';
import { TenantService } from './tenant.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'app';

  constructor(private tenantService: TenantService) { }
}
