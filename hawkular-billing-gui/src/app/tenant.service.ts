import { Injectable } from '@angular/core';
import { Tenant } from './types';

export const TENANTS: Tenant[] = [
    {name: 'gigi'},
    {name: 'cornel'},
];


@Injectable()
export class TenantService {
    getTenants(): Tenant[] {
        return TENANTS;
    }
}
