import { IsEmail, IsOptional, IsString, MinLength } from 'class-validator';

export class CreatePatientDto {
  @IsString()
  @MinLength(2)
  name: string;

  @IsString()
  @MinLength(5)
  phone: string;

  @IsOptional()
  @IsEmail()
  email?: string;

  @IsOptional()
  @IsString()
  notes?: string;
}

export class UpdatePatientDto {
  @IsOptional() @IsString() @MinLength(2) name?: string;
  @IsOptional() @IsString() @MinLength(5) phone?: string;
  @IsOptional() @IsString() email?: string;
  @IsOptional() @IsString() notes?: string;
}
